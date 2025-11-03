"""Simulovaná databáze osob s dummy daty"""
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random


class PeopleDatabase:
    """Lokální simulovaná databáze osob"""

    def __init__(self):
        self.people = self._generate_dummy_data()

    def _generate_dummy_data(self) -> List[Dict]:
        """Generuje dummy data"""

        first_names = [
            "Jan", "Petr", "Pavel", "Martin", "Tomáš", "Jakub", "Lukáš", "Ondřej",
            "Jana", "Eva", "Anna", "Petra", "Lucie", "Kateřina", "Tereza", "Barbora",
            "Jiří", "Michal", "David", "Marek"
        ]

        last_names = [
            "Novák", "Svoboda", "Novotný", "Dvořák", "Černý", "Procházka", "Kučera",
            "Veselý", "Horák", "Němec", "Pokorný", "Pospíšil", "Hájek", "Král"
        ]

        positions = [
            "Software Developer", "Senior Developer", "Team Lead", "Project Manager",
            "Data Analyst", "UX Designer", "DevOps Engineer", "QA Tester",
            "Business Analyst", "Product Owner", "Scrum Master", "Architect"
        ]

        departments = [
            "IT", "Engineering", "Sales", "Marketing", "HR", "Finance", "Operations"
        ]

        locations = [
            "Praha", "Brno", "Ostrava", "Plzeň", "Liberec", "Olomouc", "Hradec Králové"
        ]

        skills = [
            "Python", "Java", "C#", "JavaScript", "React", "Angular", "Vue.js",
            "Docker", "Kubernetes", "AWS", "Azure", "SQL", "NoSQL", "Machine Learning",
            "Data Science", "Agile", "Scrum", "Git", "CI/CD"
        ]

        people = []

        for i in range(50):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)

            # Generování datumu nástupu (poslední 3 roky)
            days_ago = random.randint(0, 1095)
            hire_date = datetime.now() - timedelta(days=days_ago)

            person = {
                "id": i + 1,
                "first_name": first_name,
                "last_name": last_name,
                "full_name": f"{first_name} {last_name}",
                "email": f"{first_name.lower()}.{last_name.lower()}{i}@company.com",
                "phone": f"+420 {random.randint(600, 799)} {random.randint(100, 999)} {random.randint(100, 999)}",
                "position": random.choice(positions),
                "department": random.choice(departments),
                "location": random.choice(locations),
                "salary": random.randint(40000, 150000),
                "hire_date": hire_date.strftime("%Y-%m-%d"),
                "age": random.randint(22, 60),
                "skills": random.sample(skills, random.randint(3, 7)),
                "active": random.random() > 0.1  # 90% aktivních
            }

            people.append(person)

        return people

    def get_all_people(self) -> List[Dict]:
        """Vrátí všechny osoby"""
        return self.people

    def get_person_by_id(self, person_id: int) -> Optional[Dict]:
        """Najde osobu podle ID"""
        for person in self.people:
            if person["id"] == person_id:
                return person
        return None

    def search_by_name(self, name: str) -> List[Dict]:
        """Vyhledá osoby podle jména"""
        name_lower = name.lower()
        results = []
        for person in self.people:
            if (name_lower in person["first_name"].lower() or
                name_lower in person["last_name"].lower() or
                name_lower in person["full_name"].lower()):
                results.append(person)
        return results

    def filter_by_department(self, department: str) -> List[Dict]:
        """Filtruje osoby podle oddělení"""
        return [p for p in self.people if p["department"].lower() == department.lower()]

    def filter_by_position(self, position: str) -> List[Dict]:
        """Filtruje osoby podle pozice"""
        position_lower = position.lower()
        return [p for p in self.people if position_lower in p["position"].lower()]

    def filter_by_location(self, location: str) -> List[Dict]:
        """Filtruje osoby podle lokace"""
        return [p for p in self.people if p["location"].lower() == location.lower()]

    def filter_by_skill(self, skill: str) -> List[Dict]:
        """Najde osoby se specifickou skillou"""
        skill_lower = skill.lower()
        results = []
        for person in self.people:
            if any(skill_lower in s.lower() for s in person["skills"]):
                results.append(person)
        return results

    def get_active_employees(self) -> List[Dict]:
        """Vrátí pouze aktivní zaměstnance"""
        return [p for p in self.people if p["active"]]

    def get_statistics(self) -> Dict:
        """Vrátí statistiky o databázi"""
        active_count = len([p for p in self.people if p["active"]])

        departments = {}
        for person in self.people:
            dept = person["department"]
            departments[dept] = departments.get(dept, 0) + 1

        positions = {}
        for person in self.people:
            pos = person["position"]
            positions[pos] = positions.get(pos, 0) + 1

        locations = {}
        for person in self.people:
            loc = person["location"]
            locations[loc] = locations.get(loc, 0) + 1

        avg_salary = sum(p["salary"] for p in self.people) / len(self.people)
        avg_age = sum(p["age"] for p in self.people) / len(self.people)

        return {
            "total_people": len(self.people),
            "active_employees": active_count,
            "inactive_employees": len(self.people) - active_count,
            "departments": departments,
            "positions": positions,
            "locations": locations,
            "average_salary": int(avg_salary),
            "average_age": int(avg_age)
        }

    def export_to_json(self) -> str:
        """Exportuje databázi do JSON"""
        return json.dumps(self.people, ensure_ascii=False, indent=2)
