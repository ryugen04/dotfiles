# Mermaid Diagram Reference

Mermaid diagrams render natively in GitHub, GitLab, VS Code, and most Markdown viewers. No external libraries or CDN imports needed.

## Basic Syntax

Wrap diagrams in a fenced code block with `mermaid` language identifier:

````markdown
```mermaid
graph TD
    A[Start] --> B[End]
```
````

## Diagram Configuration via Frontmatter

Some Markdown viewers support Mermaid frontmatter for configuration:

````markdown
```mermaid
---
config:
  look: handDrawn
  layout: elk
---
graph TD
    A[User Request] --> B{Auth Check}
    B -->|Valid| C[Process]
    B -->|Invalid| D[Reject]
```
````

**Note:** Frontmatter support varies by viewer. GitHub renders diagrams with default settings; VS Code with Mermaid extension supports more options.

## Diagram Types

### Flowchart (graph)

Direction options: `TD` (top-down), `LR` (left-right), `BT` (bottom-top), `RL` (right-left).

```mermaid
graph TD
    A[Request] --> B{Authenticated?}
    B -->|Yes| C[Load Dashboard]
    B -->|No| D[Login Page]
    D --> E[Submit Credentials]
    E --> B
    C --> F{Role?}
    F -->|Admin| G[Admin Panel]
    F -->|User| H[User Dashboard]
```

**Node shapes:**
| Syntax | Shape | Usage |
|--------|-------|-------|
| `[text]` | Rectangle | Default, general purpose |
| `(text)` | Rounded rectangle | Soft actions |
| `{text}` | Diamond | Decision points |
| `([text])` | Stadium | Start/end points |
| `[[text]]` | Subroutine | External processes |
| `[(text)]` | Cylinder | Database/storage |
| `((text))` | Circle | Connectors |
| `>text]` | Flag | Async signals |
| `{{text}}` | Hexagon | Preparation steps |

**Edge styles:**
| Syntax | Style | Usage |
|--------|-------|-------|
| `-->` | Arrow | Default flow |
| `---` | Line | Connection without direction |
| `-.->` | Dotted arrow | Optional/async flow |
| `==>` | Thick arrow | Primary/important flow |
| `--text-->` | Arrow with label | Labeled connection |
| `-->\|text\|` | Arrow with label (alt) | Labeled connection |

### Sequence Diagram

```mermaid
sequenceDiagram
    participant C as Client
    participant G as Gateway
    participant S as Service
    participant D as Database
    C->>G: POST /api/data
    G->>G: Validate JWT
    G->>S: Forward request
    S->>D: Query
    D-->>S: Results
    S-->>G: Response
    G-->>C: 200 OK
```

**Arrow types:**
| Syntax | Style |
|--------|-------|
| `->>` | Solid arrow (sync call) |
| `-->>` | Dashed arrow (async response) |
| `-x` | Solid with X (failed call) |
| `--x` | Dashed with X (failed response) |
| `-)` | Solid arrow (open end) |
| `--)` | Dashed arrow (open end) |

**Activation and notes:**
```mermaid
sequenceDiagram
    participant A as Service A
    participant B as Service B
    A->>+B: Request
    Note right of B: Processing...
    B-->>-A: Response
    Note over A,B: Transaction complete
```

### State Diagram

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Review : submit
    Review --> Approved : approve
    Review --> Draft : request_changes
    Approved --> Published : publish
    Published --> Archived : archive
    Archived --> [*]
```

**⚠️ Label limitations:** State diagram transition labels have a strict parser. Avoid:
- `<br/>` — only works in flowcharts; causes parse errors in state diagrams
- Parentheses in labels — `cancel()` can confuse the parser
- Multiple colons — the first `:` is the label delimiter; extra colons may break parsing
- HTML entities — not supported

**Workaround:** If you need multi-line labels or special characters, use `flowchart` instead with quoted labels:
```mermaid
flowchart LR
    A((Start)) --> B[Draft]
    B -->|"submit for<br/>review"| C[Review]
    C -->|"approve()"| D[Approved]
```

### ER Diagram

```mermaid
erDiagram
    USERS ||--o{ ORDERS : places
    ORDERS ||--|{ LINE_ITEMS : contains
    LINE_ITEMS }o--|| PRODUCTS : references
    USERS { string email PK }
    ORDERS { int id PK }
    LINE_ITEMS { int quantity }
    PRODUCTS { string name }
```

**Cardinality markers:**
| Syntax | Meaning |
|--------|---------|
| `\|\|` | Exactly one |
| `o\|` | Zero or one |
| `}\|` | One or more |
| `o{` | Zero or more |

### Mind Map

```mermaid
mindmap
    root((Project))
        Frontend
            React
            Next.js
            Tailwind
        Backend
            Node.js
            PostgreSQL
            Redis
        Infrastructure
            AWS
            Docker
            Terraform
```

### Class Diagram

```mermaid
classDiagram
    class User {
        +String email
        +String name
        +login()
        +logout()
    }
    class Order {
        +Int id
        +Date createdAt
        +process()
    }
    User "1" --> "*" Order : places
```

**Visibility markers:**
| Symbol | Visibility |
|--------|------------|
| `+` | Public |
| `-` | Private |
| `#` | Protected |
| `~` | Package |

### Pie Chart

```mermaid
pie title Distribution
    "Category A" : 45
    "Category B" : 30
    "Category C" : 25
```

### Gantt Chart

```mermaid
gantt
    title Project Timeline
    dateFormat  YYYY-MM-DD
    section Phase 1
    Task A           :a1, 2024-01-01, 30d
    Task B           :after a1, 20d
    section Phase 2
    Task C           :2024-02-01, 25d
```

## Styling with classDef

Define custom styles for nodes within the diagram:

```mermaid
graph TD
    A[Start]:::highlight --> B[Process]
    B --> C[End]:::success

    classDef highlight fill:#fef3c7,stroke:#d97706,stroke-width:2px
    classDef success fill:#dcfce7,stroke:#16a34a,stroke-width:2px
```

### classDef Gotchas

**1. Never set `color:` in classDef for cross-theme compatibility.**

classDef values are static — they can't use CSS variables or adapt to light/dark mode. If you set `color:#000000`, it will be unreadable in dark mode. Let the Markdown viewer handle text color automatically.

**2. Use semi-transparent fills (8-digit hex with alpha).**

Opaque fills like `fill:#fefce8` render as bright boxes in dark mode. Use alpha values for fills that work in both themes:

```
classDef highlight fill:#d9770633,stroke:#d97706,stroke-width:2px
classDef muted fill:#7c6f6422,stroke:#7c6f6488,stroke-width:1px
```

Alpha values: `11`-`33` for subtle, `44`-`77` for prominent.

**3. Border colors are more reliable than fills.**

If you want nodes to stand out across themes, use distinctive `stroke` colors rather than `fill`:

```
classDef important stroke:#dc2626,stroke-width:3px
```

## Subgraphs

Group related nodes:

```mermaid
graph TD
    subgraph Frontend
        A[React App]
        B[Redux Store]
    end
    subgraph Backend
        C[API Server]
        D[Database]
    end
    A --> C
    B --> A
    C --> D
```

Subgraphs can be nested and styled:
```mermaid
graph TD
    subgraph Cloud["Cloud Infrastructure"]
        subgraph Compute
            A[EC2]
            B[Lambda]
        end
        subgraph Storage
            C[S3]
            D[RDS]
        end
    end
    A --> C
    B --> D
```

## Notes

Add notes to sequence diagrams:

```mermaid
sequenceDiagram
    participant A
    participant B
    Note over A,B: This note spans both participants
    A->>B: Request
    Note right of B: Processing the request...
    B-->>A: Response
    Note left of A: Handle response
```

## Links in Nodes

Add clickable links (supported in some viewers):

```mermaid
graph LR
    A[Documentation] --> B[API Reference]
    click A "https://docs.example.com" "Open docs"
    click B "https://api.example.com" "Open API"
```

**Note:** Link support varies by Markdown viewer. GitHub does not render clickable links in Mermaid diagrams for security reasons.

## Tips for Markdown Output

1. **Keep diagrams focused** — Complex diagrams with 30+ nodes become hard to read. Break into multiple smaller diagrams.

2. **Use clear, short labels** — Long labels cause layout issues. Use abbreviations and provide a legend table below the diagram.

3. **Test rendering** — Check how diagrams appear in your target viewer (GitHub, VS Code, etc.). Some features render differently.

4. **Provide text fallback** — For critical information, include a text summary alongside the diagram for accessibility and search.

5. **Avoid special characters in labels** — Quotes, brackets, and angle brackets can break parsing. Use simple alphanumeric labels.

6. **Direction matters** — `TD` (top-down) works best for hierarchies and flows. `LR` (left-right) works best for timelines and pipelines.

7. **Color for meaning, not decoration** — Use classDef sparingly to highlight important nodes, not to make diagrams "pretty."
