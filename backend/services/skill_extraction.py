import re

SKILLS = [
    "Python", "Java", "C", "C++", "JavaScript", "TypeScript",
    "HTML", "CSS", "React", "Node.js", "Express.js", "FastAPI",
    "Django", "Flask", "Angular", "SQL", "NoSQL", "MongoDB",
    "PostgreSQL", "MySQL", "Git", "GitHub", "Postman",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
    "Data Analysis", "AWS", "Azure", "Docker", "Kubernetes",
]


def extract_skills(text: str) -> list[str]:
    detected_skills = []

    for skill in SKILLS:
        pattern = r"(?<![A-Za-z0-9])" + re.escape(skill) + r"(?![A-Za-z0-9])"
        if re.search(pattern, text, re.IGNORECASE):
            detected_skills.append(skill)

    return detected_skills
