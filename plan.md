{
  "project_name": "AI Learning Coach",
  "description": "Full stack web application that ingests AI related content (RSS, YouTube, X, websites), uses RAG with masterRAG.md, Supabase + pgvector, Gemini embeddings, and generates weekly personalized learning digests.",
  "stack": {
    "backend": {
      "framework": "FastAPI",
      "language": "Python 3",
      "scheduler": "APScheduler or equivalent background scheduler",
      "http_client": "httpx or requests",
      "db_client": "asyncpg or SQLAlchemy with async support"
    },
    "frontend": {
      "framework": "Next.js",
      "language": "TypeScript",
      "ui_library": "React",
      "styling": "Tailwind CSS or CSS Modules"
    },
    "database": {
      "provider": "Supabase (PostgreSQL)",
      "vector_extension": "pgvector",
      "connection": "From FastAPI using environment credentials"
    },
    "llm_and_embeddings": {
      "provider": "Gemini",
      "usage": [
        "Embeddings for goals",
        "Embeddings for internal rules (masterRAG.md)",
        "Embeddings for external content",
        "Summaries",
        "Why this matters sentences",
        "Digest body generation"
      ]
    },
    "email": {
      "provider": "MailerSend",
      "vars_from_file": "rss.md"
    }
  },
  "config_files": {
    "rag_rules_file": "masterRAG.md",
    "api_and_rss_file": "rss.md",
    "backend_api_spec": "apis.md",
    "env_file": ".env"
  },
  "env_variables_expected": {
    "from_rss_md": [
      "TWITTER_BEARER_TOKEN",
      "MAILERSEND_API_KEY",
      "MAILERSEND_FROM_EMAIL",
      "MAILERSEND_FROM_NAME",
      "MAILERSEND_ADMIN_EMAIL",
      "GOOGLE_API_KEY",
      "YOUTUBE_API_KEY"
    ],
    "from_other_sources": [
      "SUPABASE_URL",
      "SUPABASE_ANON_KEY",
      "SUPABASE_SERVICE_ROLE_KEY",
      "GEMINI_API_KEY",
      "BACKEND_BASE_URL",
      "FRONTEND_BASE_URL"
    ]
  },
  "database_model": {
    "tables": {
      "users": {
        "description": "User profiles and preferences",
        "fields": [
          "user_id (primary key)",
          "email",
          "name",
          "created_at",
          "updated_at"
        ]
      },
      "learning_goals": {
        "description": "Weekly or active learning goals per user",
        "fields": [
          "goal_id (primary key)",
          "user_id (foreign key users.user_id)",
          "goal_text",
          "difficulty_level",
          "frequency",
          "is_active",
          "created_at",
          "embedding_vector (pgvector)"
        ]
      },
      "sources": {
        "description": "User selected and system default content sources",
        "fields": [
          "source_id (primary key)",
          "user_id (nullable, null means global default source)",
          "source_type (rss, youtube, reddit, x_api, website)",
          "value (URL, channel id, subreddit name, handle, etc)",
          "status (active, disabled, error)",
          "last_fetched_at",
          "created_at"
        ]
      },
      "content_items": {
        "description": "Cleaned content units suitable for embedding",
        "fields": [
          "content_id (primary key)",
          "source_id (foreign key sources.source_id)",
          "title",
          "clean_text",
          "original_url",
          "source_type",
          "published_at",
          "fetched_at",
          "created_at"
        ]
      },
      "content_embeddings": {
        "description": "Embeddings for external content",
        "fields": [
          "embedding_id (primary key)",
          "content_id (foreign key content_items.content_id)",
          "embedding_vector (pgvector)",
          "created_at"
        ]
      },
      "internal_rag_embeddings": {
        "description": "Embeddings for chunks from masterRAG.md",
        "fields": [
          "chunk_id (primary key)",
          "section_name",
          "chunk_text",
          "embedding_vector (pgvector)",
          "created_at"
        ]
      },
      "digests": {
        "description": "Weekly digests generated per user and goal",
        "fields": [
          "digest_id (primary key)",
          "user_id (foreign key users.user_id)",
          "goal_id (foreign key learning_goals.goal_id)",
          "week_start_date",
          "week_end_date",
          "generated_at",
          "total_items"
        ]
      },
      "digest_items": {
        "description": "Individual entries inside each digest",
        "fields": [
          "digest_item_id (primary key)",
          "digest_id (foreign key digests.digest_id)",
          "content_id (foreign key content_items.content_id)",
          "title",
          "summary",
          "why_it_matters",
          "relevance_score",
          "source_type",
          "link_url"
        ]
      },
      "feedback": {
        "description": "User feedback on digest items",
        "fields": [
          "feedback_id (primary key)",
          "user_id (foreign key users.user_id)",
          "digest_item_id (foreign key digest_items.digest_item_id)",
          "content_id (foreign key content_items.content_id)",
          "feedback_value (useful, not_useful)",
          "created_at"
        ]
      },
      "system_logs": {
        "description": "System logs for ingestion, errors, and jobs",
        "fields": [
          "log_id (primary key)",
          "log_type (info, warning, error)",
          "component (ingestion, rag, email, api, scheduler)",
          "message",
          "created_at"
        ]
      }
    }
  },
  "global_rules": {
    "respect_api_spec_in_apis_md": true,
    "do_not_change_endpoint_contracts": true,
    "never_expose_secrets_to_frontend": true,
    "use_master_rag_for_all_generation_rules": true,
    "limit_digest_items_to_max": 10,
    "summaries_max_sentences": 4,
    "why_this_matters_exactly_one_sentence": true,
    "sanitize_all_ingested_html": true
  },
  "phases": [
    {
      "phase_id": "P1",
      "title": "Project and repo setup",
      "goal": "Create basic folder structure and load configuration files.",
      "steps": [
        {
          "step_id": "P1_S1",
          "summary": "Create repository layout",
          "actions": [
            "Create root folders: backend, frontend, docs, config, scripts.",
            "Place masterRAG.md in docs folder.",
            "Place rss.md and apis.md in config folder."
          ],
          "depends_on": []
        },
        {
          "step_id": "P1_S2",
          "summary": "Parse rss.md for credentials and RSS feeds",
          "actions": [
            "Read rss.md.",
            "Extract environment like TWITTER_BEARER_TOKEN, MAILERSEND_API_KEY, MAILERSEND_FROM_EMAIL, MAILERSEND_FROM_NAME, MAILERSEND_ADMIN_EMAIL, GOOGLE_API_KEY, YOUTUBE_API_KEY.",
            "Extract RSS feed URLs from AI News RSS Feeds section into a list.",
            "Write these values to a local .env file (or equivalent secret store) for backend usage."
          ],
          "depends_on": [
            "P1_S1"
          ]
        },
        {
          "step_id": "P1_S3",
          "summary": "Create .env template",
          "actions": [
            "Create backend/.env.template including Supabase and Gemini variables plus all keys drawn from rss.md.",
            "Create frontend/.env.local.template for frontend base URLs and any public configuration."
          ],
          "depends_on": [
            "P1_S2"
          ]
        }
      ]
    },
    {
      "phase_id": "P2",
      "title": "Backend FastAPI skeleton",
      "goal": "Prepare FastAPI app structure, configuration, and Supabase connectivity.",
      "steps": [
        {
          "step_id": "P2_S1",
          "summary": "Create FastAPI project structure",
          "actions": [
            "Under backend, create subfolders: app, app/api, app/core, app/models, app/services, app/rag, app/ingestion, app/schemas, app/db, app/utils.",
            "Create app/main.py as the FastAPI entry point.",
            "Create app/core/config.py to load environment variables.",
            "Create app/db/database.py for Supabase / PostgreSQL connection helpers."
          ],
          "depends_on": [
            "P1_S3"
          ]
        },
        {
          "step_id": "P2_S2",
          "summary": "Initialize FastAPI and test route",
          "actions": [
            "In main.py create a FastAPI instance.",
            "Add a simple GET /health endpoint that returns status: ok.",
            "Run the app locally and confirm health endpoint works."
          ],
          "depends_on": [
            "P2_S1"
          ]
        },
        {
          "step_id": "P2_S3",
          "summary": "Configure database connection to Supabase",
          "actions": [
            "Use SUPABASE_URL and service-level credentials (or direct Postgres URL) to configure async database client.",
            "Test a simple query such as select now() from database.",
            "Log success or failure into system_logs when possible."
          ],
          "depends_on": [
            "P2_S2"
          ]
        }
      ]
    },
    {
      "phase_id": "P3",
      "title": "Database alignment and PGVector",
      "goal": "Validate schema in Supabase and ensure pgvector is enabled.",
      "steps": [
        {
          "step_id": "P3_S1",
          "summary": "Verify pgvector extension",
          "actions": [
            "Run a query to confirm vector extension is available in Supabase.",
            "If not enabled and permitted, enable it.",
            "If not possible, log error and stop."
          ],
          "depends_on": [
            "P2_S3"
          ]
        },
        {
          "step_id": "P3_S2",
          "summary": "Validate presence of tables",
          "actions": [
            "Check that all tables defined in database_model exist in Supabase.",
            "If some are missing, either apply migration scripts or report missing tables.",
            "Ensure learning_goals, content_embeddings, internal_rag_embeddings have vector columns of the correct type."
          ],
          "depends_on": [
            "P3_S1"
          ]
        }
      ]
    },
    {
      "phase_id": "P4",
      "title": "RAG internal knowledge ingestion (masterRAG.md)",
      "goal": "Ingest rules from masterRAG.md and store embeddings in internal_rag_embeddings.",
      "steps": [
        {
          "step_id": "P4_S1",
          "summary": "Read and chunk masterRAG.md",
          "actions": [
            "Load docs/masterRAG.md.",
            "Split content into chunks of approximately 500 to 1500 characters, respecting section boundaries where possible.",
            "Label each chunk with a section_name derived from the closest markdown header."
          ],
          "depends_on": [
            "P3_S2"
          ]
        },
        {
          "step_id": "P4_S2",
          "summary": "Generate embeddings for each internal chunk",
          "actions": [
            "For each chunk_text, call Gemini embeddings API.",
            "Store embedding_vector and metadata (section_name, chunk_text) in internal_rag_embeddings."
          ],
          "depends_on": [
            "P4_S1"
          ]
        }
      ]
    },
    {
      "phase_id": "P5",
      "title": "Backend domain APIs according to apis.md",
      "goal": "Implement backend APIs for goals, sources, digests, and feedback according to existing spec.",
      "steps": [
        {
          "step_id": "P5_S1",
          "summary": "Parse apis.md and create router stubs",
          "actions": [
            "Read config/apis.md.",
            "For each endpoint defined there, create a corresponding router file in app/api (for example goals.py, sources.py, digests.py, feedback.py).",
            "Define route signatures exactly matching method, path, and payload described in apis.md. Leave implementations as placeholders initially."
          ],
          "depends_on": [
            "P2_S3"
          ]
        },
        {
          "step_id": "P5_S2",
          "summary": "Implement learning goal endpoints",
          "actions": [
            "Implement POST endpoint for creating a learning goal: insert row into learning_goals, generate embedding via Gemini, store embedding_vector, deactivate older goals for that user.",
            "Implement GET endpoint for fetching active goal for the current user.",
            "Ensure responses follow apis.md contract."
          ],
          "depends_on": [
            "P5_S1",
            "P4_S2"
          ]
        },
        {
          "step_id": "P5_S3",
          "summary": "Implement content source endpoints",
          "actions": [
            "Implement POST endpoint to add a source to sources table (rss, youtube, reddit, x_api, website).",
            "Implement GET endpoint to list sources per user, including status and last_fetched_at.",
            "Respect path and body schema defined in apis.md."
          ],
          "depends_on": [
            "P5_S1"
          ]
        },
        {
          "step_id": "P5_S4",
          "summary": "Implement digest and digest history endpoints",
          "actions": [
            "Implement GET endpoint to fetch current or latest digest for a user, joining digests with digest_items and content_items.",
            "Implement GET endpoint to list past digests, returning digest metadata and optionally counts.",
            "Ensure responses align with apis.md."
          ],
          "depends_on": [
            "P5_S1"
          ]
        },
        {
          "step_id": "P5_S5",
          "summary": "Implement feedback endpoints",
          "actions": [
            "Implement POST endpoint to record feedback on digest items (useful or not_useful).",
            "Insert row into feedback table and return confirmation.",
            "Do not yet change scoring logic here, only record events."
          ],
          "depends_on": [
            "P5_S4"
          ]
        }
      ]
    },
    {
      "phase_id": "P6",
      "title": "External content ingestion engine",
      "goal": "Ingest content from rss.md feeds and user defined sources and create external embeddings.",
      "steps": [
        {
          "step_id": "P6_S1",
          "summary": "Seed default RSS sources from rss.md",
          "actions": [
            "Take the RSS feed URLs from rss.md.",
            "Insert them into sources table as global default rows (user_id null, source_type rss).",
            "Set status to active."
          ],
          "depends_on": [
            "P5_S3"
          ]
        },
        {
          "step_id": "P6_S2",
          "summary": "Implement RSS ingestion service",
          "actions": [
            "Create app/ingestion/rss_service.py.",
            "Function: fetch all active rss sources, call RSS endpoints, parse items.",
            "For each new article, store title, description or content, URL, published date into content_items after cleaning.",
            "Avoid duplicate content based on URL or title hash."
          ],
          "depends_on": [
            "P6_S1"
          ]
        },
        {
          "step_id": "P6_S3",
          "summary": "Implement YouTube ingestion service",
          "actions": [
            "Create app/ingestion/youtube_service.py.",
            "Use YOUTUBE_API_KEY from rss.md.",
            "Fetch recent videos for each youtube type source.",
            "Store title, description, URL, published_at into content_items after cleaning."
          ],
          "depends_on": [
            "P6_S2"
          ]
        },
        {
          "step_id": "P6_S4",
          "summary": "Implement X (Twitter) ingestion service",
          "actions": [
            "Create app/ingestion/x_service.py.",
            "Use TWITTER_BEARER_TOKEN.",
            "Fetch recent tweets from configured accounts or searches stored in sources.",
            "Store cleaned tweet text and link as content_items."
          ],
          "depends_on": [
            "P6_S3"
          ]
        },
        {
          "step_id": "P6_S5",
          "summary": "Implement website scraping service",
          "actions": [
            "Create app/ingestion/web_service.py.",
            "For website type sources, fetch HTML with httpx or requests.",
            "Use a basic HTML parser to extract main content, strip scripts and noise.",
            "Store cleaned text as content_items."
          ],
          "depends_on": [
            "P6_S4"
          ]
        },
        {
          "step_id": "P6_S6",
          "summary": "Generate embeddings for external content",
          "actions": [
            "Create app/rag/embedding_service.py to handle Gemini embedding calls.",
            "For each content_items row without a corresponding entry in content_embeddings, generate embeddings and store embedding_vector.",
            "Run this periodically after ingestion jobs."
          ],
          "depends_on": [
            "P6_S5"
          ]
        },
        {
          "step_id": "P6_S7",
          "summary": "Set up scheduled ingestion and embedding jobs",
          "actions": [
            "Integrate APScheduler or similar in FastAPI startup event.",
            "Schedule ingestion jobs (RSS, YouTube, X, website) to run every 12 or 24 hours.",
            "Schedule embedding job to process newly ingested content.",
            "Log each run in system_logs."
          ],
          "depends_on": [
            "P6_S6"
          ]
        }
      ]
    },
    {
      "phase_id": "P7",
      "title": "RAG retrieval and digest generation pipeline",
      "goal": "Use masterRAG.md and external embeddings to generate weekly digests.",
      "steps": [
        {
          "step_id": "P7_S1",
          "summary": "Implement retrieval service for internal rules",
          "actions": [
            "In app/rag, create internal_retrieval.py.",
            "Implement function that takes a query describing the operation (for example digest generation) and retrieves the most relevant chunks from internal_rag_embeddings (masterRAG.md).",
            "These chunks will be included in context for generation calls."
          ],
          "depends_on": [
            "P4_S2"
          ]
        },
        {
          "step_id": "P7_S2",
          "summary": "Implement external retrieval by goal embedding",
          "actions": [
            "In app/rag, create external_retrieval.py.",
            "Given user_id and active learning_goals.embedding_vector, perform vector similarity search over content_embeddings joined with content_items and sources for that user.",
            "Return top N content_items with similarity scores."
          ],
          "depends_on": [
            "P6_S6"
          ]
        },
        {
          "step_id": "P7_S3",
          "summary": "Implement scoring and ranking per masterRAG rules",
          "actions": [
            "Create scoring module that for each candidate item combines: similarity score, keyword match against goal_text, recency bonus, and feedback adjustment if available.",
            "Implement formulas consistent with the masterRAG scoring section.",
            "Select top 5 to 10 items above a minimum score threshold."
          ],
          "depends_on": [
            "P7_S2"
          ]
        },
        {
          "step_id": "P7_S4",
          "summary": "Implement summary and why it matters generation",
          "actions": [
            "Create app/rag/summarizer.py.",
            "For each selected content item, send cleaned text and user goal to Gemini with internal rule chunks from masterRAG.md as system or additional context.",
            "Generate a 2 to 4 sentence summary and a single sentence why_it_matters string.",
            "Apply tone and style rules from masterRAG.md."
          ],
          "depends_on": [
            "P7_S1",
            "P7_S3"
          ]
        },
        {
          "step_id": "P7_S5",
          "summary": "Implement digest creation and storage",
          "actions": [
            "Create app/rag/digest_service.py.",
            "For each user with an active goal, compile selected and summarized items into a digest format.",
            "Insert digest row in digests table and digest_items rows with summary, why_it_matters, relevance_score, and link_url.",
            "Use masterRAG digest template for structure."
          ],
          "depends_on": [
            "P7_S4"
          ]
        },
        {
          "step_id": "P7_S6",
          "summary": "Schedule weekly digest generation job",
          "actions": [
            "Add a scheduler job that runs once per week.",
            "For each user with an active goal, run retrieval, scoring, summarization, and digest creation.",
            "Log success or failures in system_logs."
          ],
          "depends_on": [
            "P7_S5"
          ]
        }
      ]
    },
    {
      "phase_id": "P8",
      "title": "Email delivery with MailerSend",
      "goal": "Send digest emails to users using MailerSend and expose them in frontend.",
      "steps": [
        {
          "step_id": "P8_S1",
          "summary": "Implement email template generator",
          "actions": [
            "Create app/services/email_service.py.",
            "Build HTML layout that includes: goal_text, week range, list of digest items with title, summary, why_it_matters, and link.",
            "Use MAILERSEND_FROM_NAME and MAILERSEND_FROM_EMAIL as sender."
          ],
          "depends_on": [
            "P7_S5"
          ]
        },
        {
          "step_id": "P8_S2",
          "summary": "Integrate MailerSend API",
          "actions": [
            "Use MAILERSEND_API_KEY to call MailerSend API from email_service.",
            "After each digest generation, send email to user.email and optionally BCC MAILERSEND_ADMIN_EMAIL.",
            "Record success or failure in system_logs."
          ],
          "depends_on": [
            "P8_S1"
          ]
        }
      ]
    },
    {
      "phase_id": "P9",
      "title": "Next.js frontend implementation",
      "goal": "Build all user facing pages and connect them to FastAPI backend.",
      "steps": [
        {
          "step_id": "P9_S1",
          "summary": "Initialize Next.js app",
          "actions": [
            "Under frontend folder, bootstrap a Next.js TypeScript project.",
            "Configure base URL for backend in environment config.",
            "Install UI dependencies such as Tailwind if desired."
          ],
          "depends_on": [
            "P2_S2"
          ]
        },
        {
          "step_id": "P9_S2",
          "summary": "Implement authentication scaffolding (simple version)",
          "actions": [
            "If Supabase auth is used, integrate Supabase client in frontend to manage user sessions.",
            "Or temporarily use a single test user for MVP.",
            "Ensure each frontend request can send user context to backend."
          ],
          "depends_on": [
            "P9_S1"
          ]
        },
        {
          "step_id": "P9_S3",
          "summary": "Build Set Learning Goal page",
          "actions": [
            "Create page with text area for goal_text and select for difficulty and frequency.",
            "On submit, call FastAPI goal creation endpoint defined in apis.md.",
            "Display the active goal at top of the page."
          ],
          "depends_on": [
            "P5_S2"
          ]
        },
        {
          "step_id": "P9_S4",
          "summary": "Build Sources management page",
          "actions": [
            "Create page with forms to add RSS URL, YouTube channel, X handle, Reddit subreddit, and website URL.",
            "Submit each to sources API.",
            "List current sources with status and last_fetched_at using GET sources endpoint."
          ],
          "depends_on": [
            "P5_S3",
            "P6_S7"
          ]
        },
        {
          "step_id": "P9_S5",
          "summary": "Build Weekly Digest page",
          "actions": [
            "Create page that calls GET current digest endpoint on load.",
            "Render items as cards with title, summary, why_it_matters, link, and source type.",
            "Include Useful and Not useful buttons that call feedback endpoint."
          ],
          "depends_on": [
            "P5_S4",
            "P5_S5",
            "P7_S5"
          ]
        },
        {
          "step_id": "P9_S6",
          "summary": "Build Digest History page",
          "actions": [
            "Create page that calls digest history endpoint.",
            "List earlier digests by week and goal.",
            "Allow clicking to view a selected digest in the same layout as Weekly Digest page."
          ],
          "depends_on": [
            "P5_S4",
            "P7_S5"
          ]
        }
      ]
    },
    {
      "phase_id": "P10",
      "title": "Feedback loop and refinement",
      "goal": "Use feedback data to gradually improve relevance.",
      "steps": [
        {
          "step_id": "P10_S1",
          "summary": "Create reporting queries on feedback",
          "actions": [
            "Implement a reporting script or admin endpoint to aggregate feedback per user, per source_type, and per topic.",
            "Use this to view which content types receive more useful or not_useful labels."
          ],
          "depends_on": [
            "P5_S5"
          ]
        },
        {
          "step_id": "P10_S2",
          "summary": "Incorporate feedback into scoring",
          "actions": [
            "Adjust scoring module to add a small positive bias for items from sources and topics that have high useful ratios, and a small negative bias for those with many not_useful votes.",
            "Keep the adjustment subtle so semantic similarity remains the primary factor."
          ],
          "depends_on": [
            "P10_S1",
            "P7_S3"
          ]
        }
      ]
    },
    {
      "phase_id": "P11",
      "title": "Deployment",
      "goal": "Deploy backend and frontend for public or test access.",
      "steps": [
        {
          "step_id": "P11_S1",
          "summary": "Deploy FastAPI backend",
          "actions": [
            "Containerize backend if required.",
            "Deploy to a platform that supports FastAPI, such as Render, Fly.io, or a VM.",
            "Configure environment variables using production keys and Supabase credentials.",
            "Verify health endpoint and one API endpoint in production."
          ],
          "depends_on": [
            "P9_S5"
          ]
        },
        {
          "step_id": "P11_S2",
          "summary": "Deploy Next.js frontend",
          "actions": [
            "Deploy Next.js to Vercel or another platform.",
            "Set NEXT_PUBLIC_BACKEND_URL pointing to backend.",
            "Test Set Goal, Sources, and Weekly Digest pages end to end."
          ],
          "depends_on": [
            "P11_S1"
          ]
        }
      ]
    }
  ]
}