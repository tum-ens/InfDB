# Data Pipeline
Each tool in the InfDB infrastructure operates in its own isolated database schema, named after the tool itself. This schema isolation ensures that multiple developers can work independently without interfering with each other's data or processes.

```
PostgreSQL Database (infdb)
│
├── Schema: infdb-import          # Data import tool
│   ├── Tables
│   ├── Views
│   └── Functions
│
├── Schema: infdb-basedata        # Base data processing
│   ├── Tables
│   ├── Views
│   └── Functions
│
├── Schema: kwp                   # Analysis scripts
│   ├── Tables
│   ├── Views
│   └── Functions
│
└── Schema: choose-a-name         # Your new tool
   ├── Tables
   ├── Views
   └── Functions
```

The schema name is automatically configured from your tool name and available in SQL scripts via the `{output_schema}` template variable.