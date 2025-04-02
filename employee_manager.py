import pandas as pd
import numpy as np
import re

class EmployeeManager:
    """Class to manage employee data and operations"""
    
    def __init__(self, employee_df):
        """Initialize with employee dataframe"""
        self.employee_df = employee_df
        self.original_df = employee_df.copy()  # Keep a copy of the original data
        self._process_skills()
        
    def _process_skills(self):
        """Process the Skills column to ensure it's in the correct format"""
        # Make sure Skills column is treated as string
        self.employee_df['Skills'] = self.employee_df['Skills'].astype(str)
        
    def get_all_employees(self):
        """Return all employees"""
        return self.employee_df
    
    def get_employee_by_id(self, employee_id):
        """Get an employee by their ID"""
        employee = self.employee_df[self.employee_df['ID'] == employee_id]
        if not employee.empty:
            return employee.iloc[0].to_dict()
        return None
    
    def get_all_skills(self):
        """Extract and return all unique skills across all employees"""
        all_skills = set()
        for skills_str in self.employee_df['Skills']:
            # Split skills and remove any whitespace
            if pd.notna(skills_str):
                skills = [skill.strip() for skill in skills_str.split(',')]
                all_skills.update(skills)
        return sorted(list(all_skills))
    
    def get_all_roles(self):
        """Get all unique roles"""
        return sorted(self.employee_df['Role'].unique().tolist())
    
    def get_all_experience_levels(self):
        """Get all unique experience levels"""
        return sorted(self.employee_df['Experience'].unique().tolist())
    
    def has_skill(self, employee_id, skill):
        """Check if an employee has a specific skill"""
        employee = self.get_employee_by_id(employee_id)
        if employee and 'Skills' in employee:
            skills = [s.strip() for s in employee['Skills'].split(',')]
            return skill in skills
        return False
    
    def get_employee_skills(self, employee_id):
        """Get the list of skills for an employee"""
        employee = self.get_employee_by_id(employee_id)
        if employee and 'Skills' in employee:
            return [s.strip() for s in employee['Skills'].split(',')]
        return []
    
    def find_employees_by_skills(self, required_skills):
        """Find employees who have all the specified skills"""
        result = []
        
        for _, employee in self.employee_df.iterrows():
            employee_skills = [skill.strip() for skill in employee['Skills'].split(',')]
            # Check if all required skills are in the employee's skill set
            if all(skill in employee_skills for skill in required_skills):
                result.append(employee)
        
        if result:
            return pd.DataFrame(result)
        else:
            return pd.DataFrame()
    
    def get_filtered_employees(self, roles=None, experience_levels=None, availability_status=None):
        """Get employees filtered by role, experience, and availability"""
        filtered_df = self.employee_df.copy()
        
        if roles:
            filtered_df = filtered_df[filtered_df['Role'].isin(roles)]
        
        if experience_levels:
            filtered_df = filtered_df[filtered_df['Experience'].isin(experience_levels)]
        
        if availability_status:
            filtered_df = filtered_df[filtered_df['Availability'].isin(availability_status)]
        
        return filtered_df
    
    def update_employee_availability(self, employee_id, new_status, task_name=None):
        """Update an employee's availability status and current task"""
        if employee_id in self.employee_df['ID'].values:
            index = self.employee_df[self.employee_df['ID'] == employee_id].index[0]
            
            # Update availability status
            self.employee_df.at[index, 'Availability'] = new_status
            
            # Update current tasks if provided
            if task_name:
                current_tasks = self.employee_df.at[index, 'Current_Tasks']
                
                if pd.isna(current_tasks) or current_tasks == '':
                    self.employee_df.at[index, 'Current_Tasks'] = task_name
                else:
                    self.employee_df.at[index, 'Current_Tasks'] = f"{current_tasks}, {task_name}"
            
            return True
        return False
    
    def save_data(self, file_path=None):
        """Save the current employee data to a CSV file"""
        if file_path is None:
            file_path = 'employee_positions_dataset.csv'
        
        try:
            self.employee_df.to_csv(file_path, index=False)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
