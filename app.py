import streamlit as st
import pandas as pd
import numpy as np
import os
from employee_manager import EmployeeManager
from task_matcher import TaskMatcher

st.set_page_config(
    page_title="AI Task Assignment System",
    page_icon="🧑‍💼",
    layout="wide"
)

# Initialize session state variables if they don't exist
if 'employee_manager' not in st.session_state:
    st.session_state.employee_manager = None
if 'task_matcher' not in st.session_state:
    st.session_state.task_matcher = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'assigned_tasks' not in st.session_state:
    st.session_state.assigned_tasks = []

def load_data():
    """Load the employee dataset"""
    try:
        # Try to load from the attached_assets directory first (where it was uploaded)
        if os.path.exists('attached_assets/employee_positions_dataset.csv'):
            df = pd.read_csv('attached_assets/employee_positions_dataset.csv')
            return df
        # If not found, check in the current directory
        elif os.path.exists('employee_positions_dataset.csv'):
            df = pd.read_csv('employee_positions_dataset.csv')
            return df
        else:
            return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def initialize_system():
    """Initialize the employee manager and task matcher"""
    df = load_data()
    if df is not None:
        # Add availability status column if it doesn't exist
        if 'Availability' not in df.columns:
            df['Availability'] = 'Free'
        if 'Current_Tasks' not in df.columns:
            df['Current_Tasks'] = ''
        
        # Initialize employee manager and task matcher
        st.session_state.employee_manager = EmployeeManager(df)
        st.session_state.task_matcher = TaskMatcher(st.session_state.employee_manager)
        st.session_state.data_loaded = True
        return True
    return False

# Main application
st.title("AI Employee Task Assignment System")

# Initialize the system if not already done
if not st.session_state.data_loaded:
    with st.spinner("Loading employee data..."):
        if initialize_system():
            st.success("Employee data loaded successfully!")
        else:
            st.error("Failed to load employee data. Please make sure the CSV file is in the correct location.")

# If data is loaded, display the application interface
if st.session_state.data_loaded:
    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["Assign Task", "Search by Skills", "View All Employees", "View Assigned Tasks"])
    
    with tab1:
        st.header("Assign a Task")
        st.write("Enter task details to find the best matching employee")
        
        # Task input form
        with st.form(key="task_form"):
            task_description = st.text_area("Task Description", placeholder="Describe the task requirements...")
            required_skills = st.multiselect(
                "Required Skills", 
                options=st.session_state.employee_manager.get_all_skills(), 
                placeholder="Select required skills for this task"
            )
            task_priority = st.select_slider(
                "Task Priority", 
                options=["Low", "Medium", "High"]
            )
            task_name = st.text_input("Task Name", placeholder="Enter a name for this task")
            
            # Store selected employee in session state for post-form processing
            if 'selected_employee_id' not in st.session_state:
                st.session_state.selected_employee_id = None
            if 'selected_employee_name' not in st.session_state:
                st.session_state.selected_employee_name = None
            if 'selected_task_details' not in st.session_state:
                st.session_state.selected_task_details = {}
                
            submit_button = st.form_submit_button(label="Find Best Match")
            
            if submit_button:
                if not task_description:
                    st.error("Please provide a task description")
                elif not required_skills:
                    st.error("Please select at least one required skill")
                elif not task_name:
                    st.error("Please provide a task name")
                else:
                    # Try to find a matching employee
                    best_match = st.session_state.task_matcher.find_best_match(task_description, required_skills)
                    
                    if best_match:
                        employee_id, employee_name, match_score = best_match
                        st.success(f"Best match found: {employee_name} (ID: {employee_id}) with a match score of {match_score:.2f}")
                        
                        # Store selected employee and task details in session state
                        st.session_state.selected_employee_id = employee_id
                        st.session_state.selected_employee_name = employee_name
                        st.session_state.selected_task_details = {
                            'task_name': task_name,
                            'task_description': task_description,
                            'task_priority': task_priority
                        }
                        
                        # Display employee details
                        employee_details = st.session_state.employee_manager.get_employee_by_id(employee_id)
                        if employee_details is not None:
                            st.write(f"**Role:** {employee_details['Role']}")
                            st.write(f"**Position:** {employee_details['Position']}")
                            st.write(f"**Experience Level:** {employee_details['Experience']}")
                            st.write(f"**Skills:** {employee_details['Skills']}")
                            st.write(f"**Current Availability:** {employee_details['Availability']}")
                    else:
                        st.warning("No suitable employee found for this task with the required skills.")
        
        # Add task assignment button outside the form
        if st.session_state.selected_employee_id is not None:
            # Create a container for the assignment button
            assign_container = st.container()
            with assign_container:
                if st.button("Assign Task to This Employee"):
                    employee_id = st.session_state.selected_employee_id
                    employee_name = st.session_state.selected_employee_name
                    task_details = st.session_state.selected_task_details
                    
                    success = st.session_state.task_matcher.assign_task(
                        employee_id, 
                        task_details['task_name'], 
                        task_details['task_description'], 
                        task_details['task_priority']
                    )
                    
                    if success:
                        # Add to assigned tasks in session state
                        st.session_state.assigned_tasks.append({
                            'employee_id': employee_id,
                            'employee_name': employee_name,
                            'task_name': task_details['task_name'],
                            'task_description': task_details['task_description'],
                            'priority': task_details['task_priority'],
                            'timestamp': pd.Timestamp.now()
                        })
                        st.success(f"Task '{task_details['task_name']}' successfully assigned to {employee_name}!")
                        
                        # Reset the selected employee
                        st.session_state.selected_employee_id = None
                        st.session_state.selected_employee_name = None
                        st.session_state.selected_task_details = {}
                        
                        # Force a rerun to update the interface
                        st.rerun()
                    else:
                        st.error("Failed to assign task. Employee may be fully assigned.")
    
    with tab2:
        st.header("Search Employees by Skills")
        
        # Skill search form
        search_skills = st.multiselect(
            "Select Skills to Search",
            options=st.session_state.employee_manager.get_all_skills(),
            placeholder="Select one or more skills"
        )
        
        if search_skills:
            matching_employees = st.session_state.employee_manager.find_employees_by_skills(search_skills)
            
            if not matching_employees.empty:
                st.success(f"Found {len(matching_employees)} employees with the selected skills")
                
                # Display employees in a dataframe with color coding for availability
                def highlight_availability(s):
                    return ['background-color: #8CE99A' if val == 'Free' 
                           else 'background-color: #FFD43B' if val == 'Partially Assigned'
                           else 'background-color: #FF8787' for val in s]
                
                # Select columns to display
                display_cols = ['ID', 'Name', 'Role', 'Position', 'Experience', 'Skills', 'Availability']
                st.dataframe(matching_employees[display_cols].style.apply(
                    highlight_availability, subset=['Availability']
                ))
            else:
                st.warning("No employees found with the selected skills.")
    
    with tab3:
        st.header("All Employees")
        
        # Display filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_role = st.multiselect(
                "Filter by Role",
                options=st.session_state.employee_manager.get_all_roles(),
                placeholder="Select roles"
            )
        with col2:
            filter_experience = st.multiselect(
                "Filter by Experience",
                options=st.session_state.employee_manager.get_all_experience_levels(),
                placeholder="Select experience levels"
            )
        with col3:
            filter_availability = st.multiselect(
                "Filter by Availability",
                options=['Free', 'Partially Assigned', 'Fully Assigned'],
                placeholder="Select availability status"
            )
        
        # Get filtered employees
        filtered_employees = st.session_state.employee_manager.get_filtered_employees(
            roles=filter_role if filter_role else None,
            experience_levels=filter_experience if filter_experience else None,
            availability_status=filter_availability if filter_availability else None
        )
        
        # Display employees
        if not filtered_employees.empty:
            st.write(f"Showing {len(filtered_employees)} employees")
            
            # Function to highlight availability
            def highlight_availability(s):
                return ['background-color: #8CE99A' if val == 'Free' 
                       else 'background-color: #FFD43B' if val == 'Partially Assigned'
                       else 'background-color: #FF8787' for val in s]
            
            # Select columns to display
            display_cols = ['ID', 'Name', 'Role', 'Position', 'Experience', 'Skills', 'Availability']
            st.dataframe(filtered_employees[display_cols].style.apply(
                highlight_availability, subset=['Availability']
            ))
        else:
            st.warning("No employees match the selected filters.")
    
    with tab4:
        st.header("Task Assignment History")
        
        if st.session_state.assigned_tasks:
            # Convert assigned tasks to DataFrame for display
            tasks_df = pd.DataFrame(st.session_state.assigned_tasks)
            tasks_df['timestamp'] = pd.to_datetime(tasks_df['timestamp'])
            tasks_df = tasks_df.sort_values('timestamp', ascending=False)
            
            # Format for display
            display_tasks = tasks_df[['employee_name', 'task_name', 'priority', 'timestamp']]
            display_tasks.columns = ['Employee', 'Task', 'Priority', 'Assigned At']
            
            # Apply styling based on priority
            def highlight_priority(s):
                return ['background-color: #FF8787' if val == 'High'
                       else 'background-color: #FFD43B' if val == 'Medium'
                       else 'background-color: #8CE99A' for val in s]
            
            st.dataframe(display_tasks.style.apply(
                highlight_priority, subset=['Priority']
            ))
            
            # Option to view task details
            task_to_view = st.selectbox("Select a task to view details", 
                                        options=tasks_df['task_name'].tolist(),
                                        index=None,
                                        placeholder="Choose a task...")
            
            if task_to_view:
                task_details = tasks_df[tasks_df['task_name'] == task_to_view].iloc[0]
                st.subheader(f"Task: {task_details['task_name']}")
                st.write(f"**Assigned to:** {task_details['employee_name']}")
                st.write(f"**Priority:** {task_details['priority']}")
                st.write(f"**Assigned at:** {task_details['timestamp']}")
                st.write("**Description:**")
                st.write(task_details['task_description'])
        else:
            st.info("No tasks have been assigned yet.")

    # Add a footer
    st.markdown("---")
    st.caption("AI Employee Task Assignment System | Developed with Streamlit")
else:
    st.info("Please upload the employee_positions_dataset.csv file to continue.")
