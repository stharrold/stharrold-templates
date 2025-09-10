"""
LangGraph Academic Paper Writing System
Based on the YuiMedi paper structure with specialized agents for each section
"""

from typing import Dict, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage
import operator

# Define the state structure for the paper
class PaperState(TypedDict):
    topic: str
    research_questions: List[str]
    literature_review: Dict[str, str]  # source -> summary
    methodology: str
    analysis: str
    conclusions: str
    bibliography: List[str]
    current_section: str
    revision_notes: List[str]
    draft_version: int
    
class AcademicPaperWorkflow:
    def __init__(self, llm=None):
        self.llm = llm or ChatAnthropic(model="claude-3-5-sonnet-20241022")
        self.graph = self._build_graph()
        
    def _build_graph(self):
        workflow = StateGraph(PaperState)
        
        # Add all agent nodes
        workflow.add_node("research_coordinator", self.research_coordinator)
        workflow.add_node("literature_reviewer", self.literature_reviewer)
        workflow.add_node("methodology_designer", self.methodology_designer)
        workflow.add_node("data_analyst", self.data_analyst)
        workflow.add_node("technical_writer", self.technical_writer)
        workflow.add_node("citation_manager", self.citation_manager)
        workflow.add_node("peer_reviewer", self.peer_reviewer)
        workflow.add_node("revision_agent", self.revision_agent)
        
        # Define the workflow edges
        workflow.set_entry_point("research_coordinator")
        
        # Main writing flow
        workflow.add_edge("research_coordinator", "literature_reviewer")
        workflow.add_edge("literature_reviewer", "methodology_designer")
        workflow.add_edge("methodology_designer", "data_analyst")
        workflow.add_edge("data_analyst", "technical_writer")
        workflow.add_edge("technical_writer", "citation_manager")
        workflow.add_edge("citation_manager", "peer_reviewer")
        
        # Conditional edge for revisions
        workflow.add_conditional_edges(
            "peer_reviewer",
            self.needs_revision,
            {
                "revise": "revision_agent",
                "complete": END
            }
        )
        workflow.add_edge("revision_agent", "technical_writer")
        
        return workflow.compile()
    
    def research_coordinator(self, state: PaperState) -> PaperState:
        """Define research questions and paper structure"""
        prompt = f"""
        As a Research Coordinator, develop a comprehensive research plan for:
        Topic: {state['topic']}
        
        Generate:
        1. 3-5 specific research questions
        2. Paper structure outline
        3. Key areas for literature review
        4. Success criteria for the research
        
        Focus on healthcare analytics and natural language processing applications.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        # Parse response and update state
        state['research_questions'] = self._extract_research_questions(response.content)
        state['current_section'] = "research_planning"
        return state
    
    def literature_reviewer(self, state: PaperState) -> PaperState:
        """Conduct systematic literature review"""
        prompt = f"""
        As a Literature Review Specialist, analyze existing research for:
        Research Questions: {state['research_questions']}
        
        Provide:
        1. Summary of key papers (minimum 20 sources)
        2. Identification of research gaps
        3. Theoretical frameworks
        4. Conflicting findings in literature
        5. Trends and evolution of the field
        
        Focus on:
        - Natural language processing in healthcare
        - SQL generation from text
        - Healthcare analytics platforms
        - Workforce challenges in healthcare IT
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        # Parse literature findings
        state['literature_review'] = self._parse_literature(response.content)
        state['current_section'] = "literature_review"
        return state
    
    def methodology_designer(self, state: PaperState) -> PaperState:
        """Design research methodology"""
        prompt = f"""
        As a Methodology Expert, design the research approach for:
        Research Questions: {state['research_questions']}
        Literature Gaps: {self._summarize_gaps(state['literature_review'])}
        
        Specify:
        1. Research design (qualitative/quantitative/mixed)
        2. Data collection methods
        3. Analysis techniques
        4. Validation approaches
        5. Ethical considerations
        6. Limitations and delimitations
        
        Ensure methodology aligns with healthcare informatics standards.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        state['methodology'] = response.content
        state['current_section'] = "methodology"
        return state
    
    def data_analyst(self, state: PaperState) -> PaperState:
        """Analyze data and generate findings"""
        prompt = f"""
        As a Data Analysis Expert, analyze the research findings:
        Methodology: {state['methodology']}
        Research Questions: {state['research_questions']}
        
        Provide:
        1. Statistical analysis results
        2. Key findings with evidence
        3. Data visualizations descriptions
        4. Pattern identification
        5. Comparison with literature findings
        
        Structure findings to answer each research question systematically.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        state['analysis'] = response.content
        state['current_section'] = "analysis"
        return state
    
    def technical_writer(self, state: PaperState) -> PaperState:
        """Write the paper sections"""
        prompt = f"""
        As an Academic Technical Writer, compose the paper sections:
        
        Current Draft Version: {state.get('draft_version', 1)}
        Revision Notes: {state.get('revision_notes', [])}
        
        Write comprehensive sections for:
        1. Abstract (250 words)
        2. Introduction with problem statement
        3. Literature Review ({len(state['literature_review'])} sources)
        4. Methodology
        5. Results and Analysis
        6. Discussion
        7. Conclusions and Future Work
        
        Maintain academic tone, use proper healthcare informatics terminology,
        and ensure logical flow between sections.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        state['conclusions'] = response.content
        state['current_section'] = "writing"
        state['draft_version'] = state.get('draft_version', 0) + 1
        return state
    
    def citation_manager(self, state: PaperState) -> PaperState:
        """Format citations and bibliography"""
        prompt = f"""
        As a Citation Specialist, format all references:
        Literature Sources: {state['literature_review'].keys()}
        
        Generate:
        1. In-text citations (APA/IEEE format)
        2. Complete bibliography
        3. DOI links where applicable
        4. Proper formatting for different source types
        
        Ensure all citations follow healthcare informatics journal standards.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        state['bibliography'] = self._format_bibliography(response.content)
        state['current_section'] = "citations"
        return state
    
    def peer_reviewer(self, state: PaperState) -> PaperState:
        """Conduct peer review"""
        prompt = f"""
        As a Peer Reviewer, critically evaluate the paper:
        
        Review criteria:
        1. Research question clarity and significance
        2. Literature review comprehensiveness
        3. Methodology appropriateness
        4. Analysis rigor
        5. Conclusions validity
        6. Writing quality and organization
        7. Citation accuracy
        
        Provide:
        - Major concerns (must address)
        - Minor issues (should address)
        - Suggestions for improvement
        - Publication readiness assessment
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        state['revision_notes'] = self._extract_revision_notes(response.content)
        state['current_section'] = "review"
        return state
    
    def revision_agent(self, state: PaperState) -> PaperState:
        """Address peer review feedback"""
        prompt = f"""
        As a Revision Specialist, address the following feedback:
        Revision Notes: {state['revision_notes']}
        
        Create a revision plan that:
        1. Prioritizes major concerns
        2. Suggests specific text changes
        3. Identifies sections needing rewriting
        4. Maintains paper coherence
        5. Tracks changes for transparency
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        state['revision_notes'].append(f"Revision round {state['draft_version']}: {response.content}")
        return state
    
    def needs_revision(self, state: PaperState) -> str:
        """Determine if paper needs revision"""
        major_issues = [note for note in state.get('revision_notes', []) 
                       if 'major' in note.lower()]
        
        if len(major_issues) > 0 and state.get('draft_version', 1) < 3:
            return "revise"
        return "complete"
    
    # Helper methods
    def _extract_research_questions(self, content: str) -> List[str]:
        """Extract research questions from LLM response"""
        # Parse the response to extract research questions
        lines = content.split('\n')
        questions = []
        for line in lines:
            if '?' in line and any(marker in line.lower() for marker in ['1.', '2.', '3.', 'rq', 'question']):
                questions.append(line.strip())
        return questions[:5]  # Limit to 5 questions
    
    def _parse_literature(self, content: str) -> Dict[str, str]:
        """Parse literature review into structured format"""
        # Simple parsing - in production, use more sophisticated parsing
        literature = {}
        sections = content.split('\n\n')
        for section in sections:
            if 'et al' in section or 'Author' in section:
                # Extract paper title and summary
                lines = section.split('\n')
                if lines:
                    title = lines[0]
                    summary = ' '.join(lines[1:])
                    literature[title] = summary
        return literature
    
    def _summarize_gaps(self, literature: Dict[str, str]) -> str:
        """Summarize research gaps from literature"""
        return "Key gaps identified in current literature review"
    
    def _format_bibliography(self, content: str) -> List[str]:
        """Format bibliography entries"""
        entries = content.split('\n')
        return [entry.strip() for entry in entries if entry.strip()]
    
    def _extract_revision_notes(self, content: str) -> List[str]:
        """Extract revision notes from peer review"""
        notes = []
        for line in content.split('\n'):
            if any(marker in line.lower() for marker in ['concern', 'issue', 'improve', 'revise']):
                notes.append(line.strip())
        return notes

# Usage example
def write_academic_paper(topic: str, initial_context: dict = None):
    """
    Main function to write an academic paper using LangGraph
    
    Args:
        topic: Research topic
        initial_context: Optional context like existing literature, data, etc.
    """
    
    # Initialize the workflow
    workflow = AcademicPaperWorkflow()
    
    # Set initial state
    initial_state = {
        "topic": topic,
        "research_questions": [],
        "literature_review": initial_context.get('literature', {}) if initial_context else {},
        "methodology": "",
        "analysis": "",
        "conclusions": "",
        "bibliography": [],
        "current_section": "start",
        "revision_notes": [],
        "draft_version": 0
    }
    
    # Run the workflow
    final_state = workflow.graph.invoke(initial_state)
    
    # Export the paper
    return export_paper(final_state)

def export_paper(state: PaperState) -> dict:
    """Export the paper in various formats"""
    return {
        "markdown": generate_markdown(state),
        "latex": generate_latex(state),
        "docx_template": generate_docx_template(state),
        "metadata": {
            "version": state['draft_version'],
            "sections_completed": state['current_section'],
            "bibliography_count": len(state['bibliography']),
            "revision_rounds": len([n for n in state['revision_notes'] if 'Revision round' in n])
        }
    }

def generate_markdown(state: PaperState) -> str:
    """Generate markdown version of the paper"""
    md_content = f"""
# {state['topic']}

## Abstract
{state.get('conclusions', '').split('Abstract:')[1].split('Introduction:')[0] if 'Abstract:' in state.get('conclusions', '') else 'Abstract pending...'}

## Introduction
{state.get('conclusions', '').split('Introduction:')[1].split('Literature Review:')[0] if 'Introduction:' in state.get('conclusions', '') else 'Introduction pending...'}

## Research Questions
{chr(10).join([f"{i+1}. {q}" for i, q in enumerate(state['research_questions'])])}

## Literature Review
{format_literature_section(state['literature_review'])}

## Methodology
{state['methodology']}

## Analysis and Results
{state['analysis']}

## Conclusions
{state.get('conclusions', '').split('Conclusions:')[1] if 'Conclusions:' in state.get('conclusions', '') else 'Conclusions pending...'}

## References
{chr(10).join(state['bibliography'])}

---
*Draft Version: {state['draft_version']}*
*Last Section: {state['current_section']}*
"""
    return md_content

def format_literature_section(literature: Dict[str, str]) -> str:
    """Format literature review section"""
    sections = []
    for source, summary in literature.items():
        sections.append(f"### {source}\n{summary}\n")
    return '\n'.join(sections)

def generate_latex(state: PaperState) -> str:
    """Generate LaTeX version of the paper"""
    # Implement LaTeX generation
    return "\\documentclass{article}\n% LaTeX content here"

def generate_docx_template(state: PaperState) -> str:
    """Generate DOCX template structure"""
    # Implement DOCX template generation
    return "DOCX template structure"

# Example usage for healthcare paper like YuiMedi
if __name__ == "__main__":
    topic = "Natural Language to SQL in Healthcare: A Comprehensive Analysis of Conversational AI Platforms for Healthcare Analytics"
    
    initial_context = {
        "literature": {
            "Wang et al. (2023)": "Study on NLP applications in clinical settings...",
            "Smith et al. (2024)": "Healthcare workforce challenges in data analytics..."
        }
    }
    
    paper = write_academic_paper(topic, initial_context)
    print(paper["markdown"])