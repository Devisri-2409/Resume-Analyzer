import json
from database import SessionLocal, Base, engine
from models import Course, CourseModule, Lesson, Quiz, QuizQuestion, QuizOption, User, Profile

COURSES_DATA = [
    {
        "title": "Python for Developers",
        "slug": "python-for-developers",
        "description": "Master essential Python concepts including variables, control flow, functions, object-oriented programming, and file handling for production systems.",
        "difficulty": "Beginner",
        "estimated_duration": "4 hours",
        "skills_covered": ["Python", "Flask", "Django"],
        "category": "Backend Development",
        "order": 1,
        "modules": [
            {
                "title": "Module 1: Python Basics & Syntax",
                "order": 1,
                "lessons": [
                    {
                        "title": "Introduction & Environment Setup",
                        "order": 1,
                        "duration": "10 mins",
                        "explanation": "Python is a high-level, interpreted language designed for readability and rapid developer velocity. It uses clean indentation instead of braces to define code blocks.",
                        "examples": "# Simple greeting in Python\ndef greet(name: str) -> str:\n    return f'Hello, {name}!'\n\nprint(greet('Developer'))",
                        "important_points": [
                            "Python files use the .py extension.",
                            "Variables are dynamically typed but type hints improve clarity and IDE support.",
                            "Indentation (4 spaces) is strictly enforced for block scope."
                        ]
                    },
                    {
                        "title": "Variables, Data Types & Operators",
                        "order": 2,
                        "duration": "15 mins",
                        "explanation": "Python features built-in primitive types like int, float, bool, and str, alongside powerful collection types like list, tuple, dict, and set.",
                        "examples": "# Working with collections\nuser_profile = {\n    'name': 'Devi',\n    'skills': ['Python', 'SQL'],\n    'experience_years': 3\n}\n\n# Adding a new skill\nuser_profile['skills'].append('FastAPI')",
                        "important_points": [
                            "Lists are mutable sequences; tuples are immutable.",
                            "Dictionaries store key-value pairs with O(1) average lookup time.",
                            "F-strings (f'...') provide clean, performant string interpolation."
                        ]
                    }
                ]
            },
            {
                "title": "Module 2: Control Flow & Iterations",
                "order": 2,
                "lessons": [
                    {
                        "title": "Conditionals & Logic",
                        "order": 1,
                        "duration": "15 mins",
                        "explanation": "Control execution paths using if, elif, and else statements with logical operators (and, or, not).",
                        "examples": "score = 85\nif score >= 90:\n    grade = 'A'\nelif score >= 80:\n    grade = 'B'\nelse:\n    grade = 'C'",
                        "important_points": [
                            "Python evaluates conditions using truthy and falsy values.",
                            "Chained comparisons like 0 <= score <= 100 are native and idiomatic."
                        ]
                    },
                    {
                        "title": "Loops & List Comprehensions",
                        "order": 2,
                        "duration": "20 mins",
                        "explanation": "Iterate through sequences using for and while loops. Use list comprehensions for concise, declarative list transformations.",
                        "examples": "skills = ['python', 'fastapi', 'docker']\nuppercase_skills = [s.upper() for s in skills if len(s) > 4]\n# Output: ['PYTHON', 'FASTAPI', 'DOCKER']",
                        "important_points": [
                            "Use enumerate() when you need both index and element.",
                            "List comprehensions are typically faster than manual append loops."
                        ]
                    }
                ]
            },
            {
                "title": "Module 3: Functions & Modular Code",
                "order": 3,
                "lessons": [
                    {
                        "title": "Functions, Parameters & Return Values",
                        "order": 1,
                        "duration": "20 mins",
                        "explanation": "Functions encapsulate reusable units of logic. You can pass positional, keyword, and default arguments, and return single or multiple values.",
                        "examples": "def calculate_ats_match(user_skills: set, required_skills: set) -> dict:\n    matched = user_skills & required_skills\n    missing = required_skills - user_skills\n    rate = len(matched) / len(required_skills) if required_skills else 0\n    return {'match_rate': round(rate * 100, 1), 'missing': list(missing)}",
                        "important_points": [
                            "Functions in Python are first-class citizens and can be passed as arguments.",
                            "Docstrings directly below the function definition serve as documentation.",
                            "Default parameters should always be immutable (avoid empty list defaults)."
                        ]
                    }
                ]
            }
        ],
        "quiz": {
            "title": "Python for Developers Assessment",
            "description": "Test your grasp of Python syntax, collections, control structures, and function design.",
            "passing_score": 75,
            "questions": [
                {
                    "question_text": "Which keyword is used to define a function in Python?",
                    "options": [
                        {"option_text": "function", "is_correct": False, "explanation": "'function' is used in JavaScript, not Python."},
                        {"option_text": "def", "is_correct": True, "explanation": "'def' is Python's standard keyword for defining functions."},
                        {"option_text": "fun", "is_correct": False, "explanation": "'fun' is used in Kotlin."},
                        {"option_text": "define", "is_correct": False, "explanation": "'define' is not a Python keyword."}
                    ]
                },
                {
                    "question_text": "What is the time complexity of looking up a key in a standard Python dictionary on average?",
                    "options": [
                        {"option_text": "O(1)", "is_correct": True, "explanation": "Python dictionaries are implemented as hash tables, giving average O(1) lookup."},
                        {"option_text": "O(n)", "is_correct": False, "explanation": "O(n) occurs only in worst-case hash collisions."},
                        {"option_text": "O(log n)", "is_correct": False, "explanation": "O(log n) applies to balanced binary search trees, not hash maps."},
                        {"option_text": "O(n log n)", "is_correct": False, "explanation": "O(n log n) is sorting complexity."}
                    ]
                },
                {
                    "question_text": "Which data type in Python is immutable?",
                    "options": [
                        {"option_text": "list", "is_correct": False, "explanation": "Lists can be modified via append, pop, etc."},
                        {"option_text": "tuple", "is_correct": True, "explanation": "Tuples cannot be modified after creation."},
                        {"option_text": "dict", "is_correct": False, "explanation": "Dictionaries allow key addition and mutation."},
                        {"option_text": "set", "is_correct": False, "explanation": "Standard sets allow adding and removing elements."}
                    ]
                },
                {
                    "question_text": "What does the expression `[x * 2 for x in [1, 2, 3]]` evaluate to?",
                    "options": [
                        {"option_text": "[2, 4, 6]", "is_correct": True, "explanation": "This list comprehension doubles each item in the list."},
                        {"option_text": "[1, 2, 3, 1, 2, 3]", "is_correct": False, "explanation": "List repetition would result from `[1, 2, 3] * 2`."},
                        {"option_text": "[2, 2, 2]", "is_correct": False, "explanation": "The multiplier operates on each individual element x."},
                        {"option_text": "SyntaxError", "is_correct": False, "explanation": "The syntax is valid Python list comprehension."}
                    ]
                }
            ]
        }
    },
    {
        "title": "Java Programming Fundamentals",
        "slug": "java-programming-fundamentals",
        "description": "Build solid object-oriented programming foundations with Java. Learn classes, interfaces, inheritance, polymorphism, and Java Collections.",
        "difficulty": "Beginner",
        "estimated_duration": "5 hours",
        "skills_covered": ["Java"],
        "category": "Backend Development",
        "order": 2,
        "modules": [
            {
                "title": "Module 1: Java Basics & JVM",
                "order": 1,
                "lessons": [
                    {
                        "title": "The Java Virtual Machine & Class Structure",
                        "order": 1,
                        "duration": "15 mins",
                        "explanation": "Java compiles to bytecode (.class) which runs on any JVM, fulfilling the 'Write Once, Run Anywhere' promise.",
                        "examples": "public class Application {\n    public static void main(String[] args) {\n        System.out.println(\"Hello from Java JVM!\");\n    }\n}",
                        "important_points": [
                            "Every Java statement must end with a semicolon.",
                            "The public class name must match the .java file name.",
                            "The main method is the application entry point."
                        ]
                    }
                ]
            },
            {
                "title": "Module 2: Object-Oriented Principles",
                "order": 2,
                "lessons": [
                    {
                        "title": "Encapsulation, Classes & Objects",
                        "order": 1,
                        "duration": "20 mins",
                        "explanation": "Encapsulation hides the internal state of an object and requires all interaction to be performed through public methods (getters/setters).",
                        "examples": "public class Candidate {\n    private String name;\n    private int atsScore;\n\n    public Candidate(String name, int atsScore) {\n        this.name = name;\n        this.atsScore = atsScore;\n    }\n    public int getAtsScore() { return atsScore; }\n}",
                        "important_points": [
                            "Fields are marked private to protect data integrity.",
                            "Constructors initialize object state upon instantiation."
                        ]
                    }
                ]
            }
        ],
        "quiz": {
            "title": "Java Fundamentals Quiz",
            "description": "Assess your understanding of Java OOP concepts and runtime mechanisms.",
            "passing_score": 75,
            "questions": [
                {
                    "question_text": "Which access modifier allows access within the same package and by subclasses?",
                    "options": [
                        {"option_text": "private", "is_correct": False, "explanation": "private restricts access strictly to the declaring class."},
                        {"option_text": "protected", "is_correct": True, "explanation": "protected allows package access plus subclass access in other packages."},
                        {"option_text": "public", "is_correct": False, "explanation": "public gives universal access everywhere."},
                        {"option_text": "default", "is_correct": False, "explanation": "default modifier does not allow access from subclasses outside package."}
                    ]
                },
                {
                    "question_text": "What is bytecode in Java?",
                    "options": [
                        {"option_text": "Machine code specific to Windows", "is_correct": False, "explanation": "Bytecode is platform-independent."},
                        {"option_text": "Intermediate representation executed by the JVM", "is_correct": True, "explanation": "Java javac compiles source code to bytecode interpreted or JIT-compiled by JVM."},
                        {"option_text": "Plain text documentation", "is_correct": False, "explanation": "Javadoc handles documentation."},
                        {"option_text": "JavaScript transpile output", "is_correct": False, "explanation": "Java is completely separate from JavaScript."}
                    ]
                }
            ]
        }
    },
    {
        "title": "SQL & Database Fundamentals",
        "slug": "sql-and-database-fundamentals",
        "description": "Learn relational database design, query writing, JOIN operations, aggregations, indexing, and schema normalization with PostgreSQL & MySQL.",
        "difficulty": "Beginner",
        "estimated_duration": "4.5 hours",
        "skills_covered": ["SQL", "PostgreSQL", "MySQL"],
        "category": "Data & Databases",
        "order": 3,
        "modules": [
            {
                "title": "Module 1: Relational Queries & Filtering",
                "order": 1,
                "lessons": [
                    {
                        "title": "SELECT, WHERE, and Ordering",
                        "order": 1,
                        "duration": "15 mins",
                        "explanation": "Structured Query Language (SQL) lets you retrieve, filter, and sort tabular data in relational databases.",
                        "examples": "SELECT full_name, email, role\nFROM users\nWHERE is_active = TRUE\nORDER BY created_at DESC\nLIMIT 10;",
                        "important_points": [
                            "WHERE filters rows before grouping or aggregation.",
                            "ORDER BY sorts results ascending (ASC) or descending (DESC).",
                            "LIMIT / OFFSET restricts total returned records for pagination."
                        ]
                    }
                ]
            },
            {
                "title": "Module 2: Table Joins & Aggregations",
                "order": 2,
                "lessons": [
                    {
                        "title": "INNER, LEFT, and RIGHT JOINs",
                        "order": 1,
                        "duration": "25 mins",
                        "explanation": "JOIN clauses combine rows from two or more tables based on a related column between them.",
                        "examples": "SELECT u.full_name, c.title, e.progress_percentage\nFROM users u\nINNER JOIN course_enrollments e ON u.id = e.user_id\nINNER JOIN courses c ON e.course_id = c.id\nWHERE e.progress_percentage > 50;",
                        "important_points": [
                            "INNER JOIN returns records that have matching values in both tables.",
                            "LEFT JOIN returns all records from the left table and matched records from the right.",
                            "Always index foreign key columns for high join performance."
                        ]
                    }
                ]
            }
        ],
        "quiz": {
            "title": "SQL & Databases Quiz",
            "description": "Evaluate query writing, joins, and table constraints.",
            "passing_score": 75,
            "questions": [
                {
                    "question_text": "Which clause is used to filter records resulting from an aggregate function like COUNT() or AVG()?",
                    "options": [
                        {"option_text": "WHERE", "is_correct": False, "explanation": "WHERE filters rows before aggregation."},
                        {"option_text": "HAVING", "is_correct": True, "explanation": "HAVING filters groups created by GROUP BY after aggregation."},
                        {"option_text": "ORDER BY", "is_correct": False, "explanation": "ORDER BY controls sorting."},
                        {"option_text": "FILTER BY", "is_correct": False, "explanation": "FILTER BY is not standard SQL."}
                    ]
                },
                {
                    "question_text": "What type of JOIN returns all records from the left table even if there are no matches in the right table?",
                    "options": [
                        {"option_text": "INNER JOIN", "is_correct": False, "explanation": "INNER JOIN only returns matching rows."},
                        {"option_text": "LEFT JOIN", "is_correct": True, "explanation": "LEFT JOIN (or LEFT OUTER JOIN) preserves all rows from the left table."},
                        {"option_text": "CROSS JOIN", "is_correct": False, "explanation": "CROSS JOIN produces a Cartesian product."},
                        {"option_text": "FULL JOIN", "is_correct": False, "explanation": "FULL JOIN preserves both left and right."}
                    ]
                }
            ]
        }
    },
    {
        "title": "Data Structures & Algorithms",
        "slug": "data-structures-and-algorithms",
        "description": "Understand core computer science fundamentals: Big O analysis, arrays, hash maps, linked lists, stacks, queues, trees, and search algorithms.",
        "difficulty": "Intermediate",
        "estimated_duration": "6 hours",
        "skills_covered": ["Data Analysis", "Python", "C++"],
        "category": "Computer Science",
        "order": 4,
        "modules": [
            {
                "title": "Module 1: Complexity & Basic Structures",
                "order": 1,
                "lessons": [
                    {
                        "title": "Big O Notation & Time Complexity",
                        "order": 1,
                        "duration": "20 mins",
                        "explanation": "Big O notation describes how an algorithm's execution time or space requirements grow as the input size n increases.",
                        "examples": "# O(1) Constant time\ndef get_first(items):\n    return items[0] if items else None\n\n# O(n) Linear time\ndef find_target(items, target):\n    for item in items:\n        if item == target:\n            return True\n    return False",
                        "important_points": [
                            "O(1) < O(log n) < O(n) < O(n log n) < O(n^2).",
                            "Focus on worst-case performance when analyzing algorithms."
                        ]
                    }
                ]
            }
        ],
        "quiz": {
            "title": "Algorithms & Complexity Quiz",
            "description": "Test algorithmic thinking and computational complexity analysis.",
            "passing_score": 75,
            "questions": [
                {
                    "question_text": "What is the average time complexity of Binary Search on a sorted array of size n?",
                    "options": [
                        {"option_text": "O(n)", "is_correct": False, "explanation": "Linear search is O(n)."},
                        {"option_text": "O(log n)", "is_correct": True, "explanation": "Binary search halves the search space at each iteration, resulting in O(log n)."},
                        {"option_text": "O(1)", "is_correct": False, "explanation": "O(1) is only achievable in hash lookups."},
                        {"option_text": "O(n log n)", "is_correct": False, "explanation": "O(n log n) is sorting complexity."}
                    ]
                }
            ]
        }
    },
    {
        "title": "Web Development Fundamentals",
        "slug": "web-development-fundamentals",
        "description": "Learn semantic HTML5, modern CSS flexbox & grid, and responsive styling to build accessible and visually polished web interfaces.",
        "difficulty": "Beginner",
        "estimated_duration": "3.5 hours",
        "skills_covered": ["HTML", "CSS", "JavaScript"],
        "category": "Frontend Development",
        "order": 5,
        "modules": [
            {
                "title": "Module 1: Semantic HTML & Accessibility",
                "order": 1,
                "lessons": [
                    {
                        "title": "Modern HTML5 Document Architecture",
                        "order": 1,
                        "duration": "15 mins",
                        "explanation": "Semantic markup gives meaning to content, improving SEO and screen reader accessibility for assistive technologies.",
                        "examples": "<article class=\"course-card\">\n  <header>\n    <h2>Python for Developers</h2>\n    <span class=\"badge\">Beginner</span>\n  </header>\n  <p>Learn core Python syntax and OOP patterns.</p>\n  <button type=\"button\">Enroll Now</button>\n</article>",
                        "important_points": [
                            "Use <header>, <nav>, <main>, <section>, and <article> appropriately.",
                            "Always provide alt attributes for images."
                        ]
                    }
                ]
            }
        ],
        "quiz": {
            "title": "Web Fundamentals Assessment",
            "description": "Review semantic markup and layout mechanics.",
            "passing_score": 75,
            "questions": [
                {
                    "question_text": "Which CSS layout mode is best suited for 1-dimensional row or column layouts?",
                    "options": [
                        {"option_text": "Flexbox", "is_correct": True, "explanation": "Flexbox is designed for 1-dimensional layouts (row or column)."},
                        {"option_text": "CSS Grid", "is_correct": False, "explanation": "CSS Grid is primarily 2-dimensional (rows and columns simultaneously)."},
                        {"option_text": "Float", "is_correct": False, "explanation": "Float is an outdated layout technique."},
                        {"option_text": "Table layout", "is_correct": False, "explanation": "Table layout is rigid and not recommended for responsive design."}
                    ]
                }
            ]
        }
    },
    {
        "title": "React & Frontend Development",
        "slug": "react-and-frontend-development",
        "description": "Master component-driven architecture, JSX syntax, React Hooks (useState, useEffect, useMemo), state management, and API integration.",
        "difficulty": "Intermediate",
        "estimated_duration": "5.5 hours",
        "skills_covered": ["React", "JavaScript", "TypeScript"],
        "category": "Frontend Development",
        "order": 6,
        "modules": [
            {
                "title": "Module 1: Components, Props & State",
                "order": 1,
                "lessons": [
                    {
                        "title": "Building Reactive Components & Managing State",
                        "order": 1,
                        "duration": "20 mins",
                        "explanation": "React components are pure functions that take props and return JSX. State variables trigger component re-renders when updated.",
                        "examples": "import { useState } from 'react';\n\nfunction ProgressCard({ courseTitle, initialProgress }) {\n  const [progress, setProgress] = useState(initialProgress);\n  return (\n    <div className='card'>\n      <h3>{courseTitle}</h3>\n      <p>Progress: {progress}%</p>\n    </div>\n  );\n}",
                        "important_points": [
                            "State updates are asynchronous and batched.",
                            "Never mutate state directly; always use the setter function."
                        ]
                    }
                ]
            }
        ],
        "quiz": {
            "title": "React Knowledge Check",
            "description": "Assess React component lifecycle, hooks, and virtual DOM concepts.",
            "passing_score": 75,
            "questions": [
                {
                    "question_text": "Which Hook should be used to run side effects such as data fetching after rendering?",
                    "options": [
                        {"option_text": "useState", "is_correct": False, "explanation": "useState manages reactive state."},
                        {"option_text": "useEffect", "is_correct": True, "explanation": "useEffect lets you synchronize a component with external systems and run effects."},
                        {"option_text": "useReducer", "is_correct": False, "explanation": "useReducer is an alternative to useState for complex logic."},
                        {"option_text": "useRef", "is_correct": False, "explanation": "useRef holds mutable values that do not trigger re-renders."}
                    ]
                }
            ]
        }
    },
    {
        "title": "REST API Development",
        "slug": "rest-api-development",
        "description": "Design secure, robust, and scalable HTTP APIs using FastAPI and Node.js. Learn HTTP status codes, authentication, request validation, and OpenAPI documentation.",
        "difficulty": "Intermediate",
        "estimated_duration": "4.5 hours",
        "skills_covered": ["FastAPI", "Node.js", "Express.js", "Postman"],
        "category": "Backend Development",
        "order": 7,
        "modules": [
            {
                "title": "Module 1: REST Principles & HTTP Standards",
                "order": 1,
                "lessons": [
                    {
                        "title": "HTTP Methods, Status Codes & REST Conventions",
                        "order": 1,
                        "duration": "20 mins",
                        "explanation": "REST leverages HTTP methods (GET, POST, PUT, DELETE) and standardized status codes (200, 201, 400, 401, 403, 404, 500) to create predictable web services.",
                        "examples": "from fastapi import FastAPI, HTTPException\n\napp = FastAPI()\n\n@app.get('/api/skills/{skill_id}')\ndef get_skill(skill_id: int):\n    if skill_id > 100:\n        raise HTTPException(status_code=404, detail='Skill not found')\n    return {'id': skill_id, 'name': 'FastAPI'}",
                        "important_points": [
                            "GET is safe and idempotent.",
                            "POST creates resources; PUT replaces; PATCH updates partially.",
                            "201 Created indicates successful creation of a new entity."
                        ]
                    }
                ]
            }
        ],
        "quiz": {
            "title": "REST API Fundamentals Quiz",
            "description": "Test understanding of REST design patterns and HTTP specifications.",
            "passing_score": 75,
            "questions": [
                {
                    "question_text": "Which HTTP status code is standard for successfully creating a new resource via POST?",
                    "options": [
                        {"option_text": "200 OK", "is_correct": False, "explanation": "200 is general success, but 201 is standard for resource creation."},
                        {"option_text": "201 Created", "is_correct": True, "explanation": "201 Created signifies that a new resource has been successfully generated."},
                        {"option_text": "204 No Content", "is_correct": False, "explanation": "204 is used when the server returns no body."},
                        {"option_text": "301 Moved Permanently", "is_correct": False, "explanation": "301 is a redirection code."}
                    ]
                }
            ]
        }
    },
    {
        "title": "Git & GitHub",
        "slug": "git-and-github",
        "description": "Master distributed version control with Git. Learn commits, branching strategies, merge conflicts, pull requests, and collaborative code reviews on GitHub.",
        "difficulty": "Beginner",
        "estimated_duration": "3 hours",
        "skills_covered": ["Git", "GitHub"],
        "category": "DevOps & Tools",
        "order": 8,
        "modules": [
            {
                "title": "Module 1: Essential Git Workflow",
                "order": 1,
                "lessons": [
                    {
                        "title": "Staging, Commits & History",
                        "order": 1,
                        "duration": "15 mins",
                        "explanation": "Git tracks changes to code over time through snapshots called commits, enabling rollbacks, branching, and team collaboration.",
                        "examples": "# Initialize and commit changes\ngit init\ngit add .\ngit commit -m 'feat: implement skill gap recommendation engine'\ngit push origin main",
                        "important_points": [
                            "Use meaningful commit messages following conventional commits.",
                            "Keep git feature branches small and focused."
                        ]
                    }
                ]
            }
        ],
        "quiz": {
            "title": "Git & GitHub Workflow Quiz",
            "description": "Test your mastery of version control operations and branch management.",
            "passing_score": 75,
            "questions": [
                {
                    "question_text": "Which command creates a new branch and switches to it in a single step?",
                    "options": [
                        {"option_text": "git checkout -b new-feature", "is_correct": True, "explanation": "git checkout -b creates the branch and immediately checks it out."},
                        {"option_text": "git branch new-feature", "is_correct": False, "explanation": "git branch only creates the branch without switching to it."},
                        {"option_text": "git merge new-feature", "is_correct": False, "explanation": "git merge combines branches."},
                        {"option_text": "git pull new-feature", "is_correct": False, "explanation": "git pull fetches and merges remote changes."}
                    ]
                }
            ]
        }
    },
    {
        "title": "Docker Fundamentals",
        "slug": "docker-fundamentals",
        "description": "Containerize full-stack applications with Docker. Learn Dockerfiles, container lifecycles, port forwarding, bind mounts, and multi-container Docker Compose setups.",
        "difficulty": "Intermediate",
        "estimated_duration": "4.5 hours",
        "skills_covered": ["Docker", "Kubernetes"],
        "category": "DevOps & Cloud",
        "order": 9,
        "modules": [
            {
                "title": "Module 1: Images, Containers & Dockerfile",
                "order": 1,
                "lessons": [
                    {
                        "title": "Writing Clean Dockerfiles",
                        "order": 1,
                        "duration": "20 mins",
                        "explanation": "Docker packages applications and their exact runtime dependencies into lightweight containers, eliminating 'it works on my machine' issues.",
                        "examples": "FROM python:3.11-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nCMD [\"uvicorn\", \"main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]",
                        "important_points": [
                            "Order Dockerfile commands from least to most frequently modified for optimal layer caching.",
                            "Use multi-stage builds to minimize production image size."
                        ]
                    }
                ]
            }
        ],
        "quiz": {
            "title": "Docker Architecture Assessment",
            "description": "Verify container fundamentals, layer caching, and networking knowledge.",
            "passing_score": 75,
            "questions": [
                {
                    "question_text": "What is the primary difference between a Docker image and a Docker container?",
                    "options": [
                        {"option_text": "An image is a read-only blueprint; a container is a runnable, isolated instance of an image", "is_correct": True, "explanation": "Images serve as immutable templates, whereas containers are running instances with a read-write layer."},
                        {"option_text": "Images run on servers; containers only run locally", "is_correct": False, "explanation": "Both run in any Docker-supported environment."},
                        {"option_text": "There is no difference", "is_correct": False, "explanation": "They represent distinct lifecycle states."},
                        {"option_text": "Containers require virtual machines", "is_correct": False, "explanation": "Containers share the host OS kernel."}
                    ]
                }
            ]
        }
    },
    {
        "title": "AWS Fundamentals",
        "slug": "aws-fundamentals",
        "description": "Explore core Amazon Web Services cloud architecture: EC2 virtual servers, S3 object storage, IAM security policies, RDS managed databases, and serverless Lambda.",
        "difficulty": "Intermediate",
        "estimated_duration": "5 hours",
        "skills_covered": ["AWS", "Azure"],
        "category": "Cloud Computing",
        "order": 10,
        "modules": [
            {
                "title": "Module 1: Cloud Architecture & Core Services",
                "order": 1,
                "lessons": [
                    {
                        "title": "Compute, Storage & Identity (IAM, EC2, S3)",
                        "order": 1,
                        "duration": "25 mins",
                        "explanation": "AWS provides on-demand cloud computing resources. IAM governs identities and access permissions, EC2 provides scalable compute instances, and S3 offers highly available object storage.",
                        "examples": "import boto3\n\ns3 = boto3.client('s3')\n# Upload a resume PDF to an S3 bucket\ns3.upload_file('resume.pdf', 'career-resumes-bucket', 'user_1_resume.pdf')",
                        "important_points": [
                            "Always apply the principle of least privilege in IAM policies.",
                            "S3 provides 99.999999999% (11 nines) of durability for stored objects."
                        ]
                    }
                ]
            }
        ],
        "quiz": {
            "title": "AWS Cloud Practitioner Quiz",
            "description": "Assess core cloud concepts, security practices, and infrastructure models.",
            "passing_score": 75,
            "questions": [
                {
                    "question_text": "Which AWS service is designed for scalable, distributed object storage (ideal for PDFs, images, and backups)?",
                    "options": [
                        {"option_text": "Amazon S3", "is_correct": True, "explanation": "Amazon Simple Storage Service (S3) is an industry-standard object storage service."},
                        {"option_text": "Amazon EC2", "is_correct": False, "explanation": "EC2 provides virtual servers."},
                        {"option_text": "Amazon RDS", "is_correct": False, "explanation": "RDS provides relational databases."},
                        {"option_text": "Amazon SQS", "is_correct": False, "explanation": "SQS is a message queuing service."}
                    ]
                }
            ]
        }
    }
]


def seed_courses():
    db = SessionLocal()
    try:
        # Check if courses already exist
        existing_count = db.query(Course).count()
        if existing_count >= 10:
            print(f"Courses already seeded ({existing_count} courses).")
            return

        for c_data in COURSES_DATA:
            existing = db.query(Course).filter(Course.slug == c_data["slug"]).first()
            if existing:
                continue

            course = Course(
                title=c_data["title"],
                slug=c_data["slug"],
                description=c_data["description"],
                difficulty=c_data["difficulty"],
                estimated_duration=c_data["estimated_duration"],
                skills_covered=json.dumps(c_data["skills_covered"]),
                category=c_data["category"],
                order=c_data["order"],
            )
            db.add(course)
            db.flush()

            # Add modules and lessons
            for m_data in c_data.get("modules", []):
                module = CourseModule(
                    course_id=course.id,
                    title=m_data["title"],
                    order=m_data["order"],
                )
                db.add(module)
                db.flush()

                for l_data in m_data.get("lessons", []):
                    lesson = Lesson(
                        course_id=course.id,
                        module_id=module.id,
                        title=l_data["title"],
                        order=l_data["order"],
                        duration=l_data.get("duration", "15 mins"),
                        explanation=l_data["explanation"],
                        examples=l_data.get("examples", ""),
                        important_points=json.dumps(l_data.get("important_points", [])),
                    )
                    db.add(lesson)

            # Add quiz
            q_data = c_data.get("quiz")
            if q_data:
                quiz = Quiz(
                    course_id=course.id,
                    title=q_data["title"],
                    description=q_data.get("description", ""),
                    passing_score=q_data.get("passing_score", 70),
                    order=1,
                )
                db.add(quiz)
                db.flush()

                for q_idx, q_item in enumerate(q_data.get("questions", []), start=1):
                    question = QuizQuestion(
                        quiz_id=quiz.id,
                        question_text=q_item["question_text"],
                        order=q_idx,
                    )
                    db.add(question)
                    db.flush()

                    for opt in q_item.get("options", []):
                        option = QuizOption(
                            question_id=question.id,
                            option_text=opt["option_text"],
                            is_correct=opt["is_correct"],
                            explanation=opt.get("explanation", ""),
                        )
                        db.add(option)

        db.commit()
        print("Successfully seeded courses, modules, lessons, and quizzes!")

        # Also create initial Profile records for any existing users without a profile
        users = db.query(User).all()
        for u in users:
            prof = db.query(Profile).filter(Profile.user_id == u.id).first()
            if not prof:
                new_prof = Profile(
                    user_id=u.id,
                    bio="Passionate technologist eager to improve software engineering and cloud skills.",
                    location="Hyderabad, India",
                )
                db.add(new_prof)
        db.commit()
        print("User profiles initialized.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed_courses()

