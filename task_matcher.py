import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TaskMatcher:
    """Class to match tasks to employees based on skills, availability, and personalized preferences"""
    
    def __init__(self, employee_manager):
        """Initialize with employee manager"""
        self.employee_manager = employee_manager
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.employee_preferences = {}
        self.task_history = {}
        self.skill_affinities = {}
    
    def analyze_task_history(self, task_history, employee_performance):
        """Analyze task history to learn employee preferences and performance patterns"""
        if not task_history:
            return False
            
        # Create dictionaries to track employee preferences
        skill_affinities = {}
        task_type_preferences = {}
        completion_speed = {}
        
        # Analyze completed tasks
        for task in task_history:
            if task.get('status') == 'Completed':
                employee_id = task.get('employee_id')
                skills = task.get('required_skills', [])
                
                if employee_id not in skill_affinities:
                    skill_affinities[employee_id] = {}
                
                # Track skills the employee has successfully completed
                for skill in skills:
                    if skill not in skill_affinities[employee_id]:
                        skill_affinities[employee_id][skill] = {
                            'count': 0,
                            'completion_time': [],
                            'success_rate': 1.0
                        }
                    
                    skill_affinities[employee_id][skill]['count'] += 1
                    
                    # If task has completion time, track it
                    if 'completion_time' in task and 'timestamp' in task:
                        time_taken = (task['completion_time'] - task['timestamp']).total_seconds() / (60 * 60)  # hours
                        skill_affinities[employee_id][skill]['completion_time'].append(time_taken)
        
        # Calculate average completion times and success rates
        for employee_id, skills in skill_affinities.items():
            for skill, data in skills.items():
                if data['completion_time']:
                    data['avg_completion_time'] = sum(data['completion_time']) / len(data['completion_time'])
                else:
                    data['avg_completion_time'] = None
        
        self.skill_affinities = skill_affinities
        return True
    
    def get_preference_score(self, employee_id, required_skills, task_description, manual_preferences=None):
        """Calculate preference score based on historical data and manual preferences"""
        preference_score = 1.0  # Default neutral score
        
        # Factor 1: Learned preferences from task history
        if employee_id in self.skill_affinities:
            skill_matches = 0
            avg_skill_count = 0
            
            for skill in required_skills:
                if skill in self.skill_affinities[employee_id]:
                    skill_data = self.skill_affinities[employee_id][skill]
                    skill_matches += 1
                    avg_skill_count += skill_data['count']
            
            if skill_matches > 0:
                # Higher preference for skills they've done more frequently
                preference_score = 1.0 + (avg_skill_count / skill_matches) * 0.1
        
        # Factor 2: Manual preferences set by managers
        if manual_preferences and employee_id in manual_preferences:
            manual_pref_score = 0.0
            manual_pref_count = 0
            
            for skill in required_skills:
                if skill in manual_preferences[employee_id]:
                    # Calculate score based on preference level (1-10 scale)
                    pref_level = manual_preferences[employee_id][skill]
                    manual_pref_score += pref_level / 10.0  # Normalize to 0-1 range
                    manual_pref_count += 1
                    
            if manual_pref_count > 0:
                # Average the manual preference scores and apply as a multiplier
                avg_manual_pref = manual_pref_score / manual_pref_count
                # Apply stronger weight to manual preferences (0.5 to 1.5 range)
                manual_factor = 0.5 + avg_manual_pref
                preference_score *= manual_factor
        
        return preference_score
    
    def find_best_match(self, task_description, required_skills, consider_preferences=True):
        """Find the best employee match for a task based on skills, availability, and preferences"""
        # First, filter employees by required skills
        employees_with_skills = self.employee_manager.find_employees_by_skills(required_skills)
        
        if employees_with_skills.empty:
            return None
        
        # Create a similarity score for each employee based on their skills
        scores = []
        for _, employee in employees_with_skills.iterrows():
            employee_id = employee['ID']
            
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
            
            # Get preference score if enabled
            preference_factor = 1.0
            if consider_preferences:
                preference_factor = self.get_preference_score(employee_id, required_skills, task_description)
                
            # Calculate final score with all factors
            total_score = skill_match_ratio * availability_factor * experience_factor * preference_factor
            scores.append((employee_id, employee['Name'], total_score))
        
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
