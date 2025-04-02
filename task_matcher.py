import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TaskMatcher:
    """Class to match tasks to employees based on skills and availability"""
    
    def __init__(self, employee_manager):
        """Initialize with employee manager"""
        self.employee_manager = employee_manager
        self.vectorizer = TfidfVectorizer(stop_words='english')
    
    def find_best_match(self, task_description, required_skills):
        """Find the best employee match for a task based on skills and availability"""
        # First, filter employees by required skills
        employees_with_skills = self.employee_manager.find_employees_by_skills(required_skills)
        
        if employees_with_skills.empty:
            return None
        
        # Create a similarity score for each employee based on their skills
        scores = []
        for _, employee in employees_with_skills.iterrows():
            # Calculate skill match score
            employee_skills = [skill.strip() for skill in employee['Skills'].split(',')]
            skill_match_ratio = len(set(required_skills).intersection(set(employee_skills))) / len(required_skills)
            
            # Adjust score based on availability
            availability_factor = 1.0  # Free
            if employee['Availability'] == 'Partially Assigned':
                availability_factor = 0.7
            elif employee['Availability'] == 'Fully Assigned':
                availability_factor = 0.3
                
            # Adjust score based on experience level
            experience_factor = 1.0  # Default
            if employee['Experience'] == 'Junior':
                experience_factor = 0.8
            elif employee['Experience'] == 'Mid-Level':
                experience_factor = 0.9
            elif employee['Experience'] == 'Senior':
                experience_factor = 1.1
            elif employee['Experience'] == 'Expert':
                experience_factor = 1.2
                
            # Calculate final score
            total_score = skill_match_ratio * availability_factor * experience_factor
            scores.append((employee['ID'], employee['Name'], total_score))
        
        # Sort by score (descending)
        scores.sort(key=lambda x: x[2], reverse=True)
        
        # Return the best match
        if scores:
            return scores[0]
        return None
    
    def assign_task(self, employee_id, task_name, task_description, priority):
        """Assign a task to an employee and update their availability"""
        employee = self.employee_manager.get_employee_by_id(employee_id)
        
        if not employee:
            return False
        
        current_availability = employee['Availability']
        
        # Determine new availability status based on current status and task priority
        new_status = current_availability
        if current_availability == 'Free':
            new_status = 'Partially Assigned'
        elif current_availability == 'Partially Assigned':
            # If priority is high or already has tasks, mark as fully assigned
            if priority == 'High':
                new_status = 'Fully Assigned'
        elif current_availability == 'Fully Assigned':
            # Cannot assign more tasks
            return False
        
        # Update employee status
        success = self.employee_manager.update_employee_availability(
            employee_id, new_status, task_name
        )
        
        # Save changes to CSV
        if success:
            self.employee_manager.save_data()
        
        return success
