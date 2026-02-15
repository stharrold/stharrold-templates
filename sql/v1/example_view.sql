-- Example SQL file demonstrating the SP + EXEC + VIEW pattern.
-- TODO: Customize -- replace with your project's stored procedures.
--
-- Pattern:
--   1. CREATE OR ALTER PROCEDURE with PRINT JSON status
--   2. EXEC the procedure
--   3. CREATE OR ALTER VIEW for reporting consumption

-- Utility function example
CREATE OR ALTER FUNCTION [dbo].[Example_Utils_v1_Parse_FN] (
    @InputString NVARCHAR(MAX),
    @Delimiter   NVARCHAR(10)
)
RETURNS NVARCHAR(MAX)
AS
BEGIN
    -- Simple parse: return first token before delimiter
    DECLARE @Result NVARCHAR(MAX);
    SET @Result = LEFT(@InputString, CHARINDEX(@Delimiter, @InputString + @Delimiter) - 1);
    RETURN @Result;
END;

GO

-- Stored procedure with PRINT JSON status output
CREATE OR ALTER PROCEDURE [dbo].[Example_Report_v1_SP]
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @StartTime DATETIME2 = SYSDATETIME();
    DECLARE @RowCount INT;

    -- Create or replace the staging table
    IF OBJECT_ID('tempdb..#Example_Staging') IS NOT NULL
        DROP TABLE #Example_Staging;

    SELECT
        t.[name]         AS [TableName],
        s.[name]         AS [SchemaName],
        p.[rows]         AS [RowCount],
        t.[create_date]  AS [CreatedDate]
    INTO #Example_Staging
    FROM sys.tables t
    INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
    INNER JOIN sys.partitions p ON t.object_id = p.object_id AND p.index_id <= 1;

    SET @RowCount = @@ROWCOUNT;

    -- Print JSON status (captured by Python orchestrator)
    DECLARE @StatusJson NVARCHAR(MAX) = (
        SELECT
            'Example_Report_v1_SP' AS [procedure],
            @RowCount              AS [rows_affected],
            DATEDIFF(MILLISECOND, @StartTime, SYSDATETIME()) AS [duration_ms]
        FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
    );
    PRINT @StatusJson;
END;

GO

-- Execute the procedure
EXEC [dbo].[Example_Report_v1_SP];

GO

-- Create the reporting view
CREATE OR ALTER VIEW [dbo].[Example_Report_v1]
AS
SELECT
    t.[name]         AS [TableName],
    s.[name]         AS [SchemaName],
    p.[rows]         AS [RowCount],
    t.[create_date]  AS [CreatedDate]
FROM sys.tables t
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
INNER JOIN sys.partitions p ON t.object_id = p.object_id AND p.index_id <= 1;

GO
