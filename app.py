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
if 'completed_tasks' not in st.session_state:
    st.session_state.completed_tasks = []
if 'employee_performance' not in st.session_state:
    st.session_state.employee_performance = {}

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

# Helper function to update employee performance metrics
def update_employee_performance(employee_id, employee_name, task_priority, completion_time):
    """Update employee performance metrics when a task is completed"""
    if employee_id not in st.session_state.employee_performance:
        st.session_state.employee_performance[employee_id] = {
            'employee_id': employee_id,
            'employee_name': employee_name,
            'tasks_completed': 0,
            'high_priority_completed': 0,
            'medium_priority_completed': 0,
            'low_priority_completed': 0,
            'avg_completion_time': 0,
            'total_completion_time': 0,
            'on_time_completion_rate': 100.0,
            'on_time_count': 0,
            'late_count': 0
        }
    
    # Update metrics
    perf = st.session_state.employee_performance[employee_id]
    perf['tasks_completed'] += 1
    
    # Update priority counts
    if task_priority == 'High':
        perf['high_priority_completed'] += 1
    elif task_priority == 'Medium':
        perf['medium_priority_completed'] += 1
    else:
        perf['low_priority_completed'] += 1
    
    # Update completion time metrics
    perf['total_completion_time'] += completion_time.total_seconds() / (60 * 60 * 24)  # Convert to days
    perf['avg_completion_time'] = perf['total_completion_time'] / perf['tasks_completed']

# If data is loaded, display the application interface
if st.session_state.data_loaded:
    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Assign Task", "Search by Skills", "View All Employees", "View Assigned Tasks", "Performance Leaderboard"])
    
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
            task_deadline = st.date_input("Deadline", min_value=pd.Timestamp.now().date())
            
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
                            'task_priority': task_priority,
                            'task_deadline': task_deadline
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
                        task_id = len(st.session_state.assigned_tasks) + 1
                        st.session_state.assigned_tasks.append({
                            'task_id': task_id,
                            'employee_id': employee_id,
                            'employee_name': employee_name,
                            'task_name': task_details['task_name'],
                            'task_description': task_details['task_description'],
                            'priority': task_details['task_priority'],
                            'deadline': task_details['task_deadline'],
                            'timestamp': pd.Timestamp.now(),
                            'status': 'In Progress'
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
            display_tasks = tasks_df[['employee_name', 'task_name', 'priority', 'deadline', 'timestamp', 'status']]
            display_tasks.columns = ['Employee', 'Task', 'Priority', 'Deadline', 'Assigned At', 'Status']
            
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
                task_id = task_details['task_id']
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"Task: {task_details['task_name']}")
                    st.write(f"**Assigned to:** {task_details['employee_name']}")
                    st.write(f"**Priority:** {task_details['priority']}")
                    st.write(f"**Deadline:** {task_details['deadline'].strftime('%Y-%m-%d')}")
                    st.write(f"**Assigned at:** {task_details['timestamp']}")
                    st.write(f"**Status:** {task_details['status']}")
                    st.write("**Description:**")
                    st.write(task_details['task_description'])
                
                # Add task completion button if task is in progress
                with col2:
                    if task_details['status'] == 'In Progress':
                        if st.button(f"Mark as Completed", key=f"complete_{task_id}"):
                            # Get task index
                            task_idx = next((i for i, task in enumerate(st.session_state.assigned_tasks) 
                                           if task['task_id'] == task_id), None)
                            
                            if task_idx is not None:
                                # Update task status
                                st.session_state.assigned_tasks[task_idx]['status'] = 'Completed'
                                st.session_state.assigned_tasks[task_idx]['completion_time'] = pd.Timestamp.now()
                                
                                # Calculate completion time
                                assigned_time = task_details['timestamp']
                                completion_time = pd.Timestamp.now()
                                time_taken = completion_time - assigned_time
                                
                                # Check if completed on time
                                deadline = pd.Timestamp(task_details['deadline'])
                                on_time = completion_time <= deadline
                                
                                # Update employee performance metrics
                                update_employee_performance(
                                    task_details['employee_id'],
                                    task_details['employee_name'],
                                    task_details['priority'],
                                    time_taken
                                )
                                
                                # Update on-time completion rate
                                if task_details['employee_id'] in st.session_state.employee_performance:
                                    perf = st.session_state.employee_performance[task_details['employee_id']]
                                    if on_time:
                                        perf['on_time_count'] += 1
                                    else:
                                        perf['late_count'] += 1
                                    
                                    total_completed = perf['on_time_count'] + perf['late_count']
                                    if total_completed > 0:
                                        perf['on_time_completion_rate'] = (perf['on_time_count'] / total_completed) * 100
                                
                                st.success(f"Task marked as completed!")
                                st.rerun()
        else:
            st.info("No tasks have been assigned yet.")

    with tab5:
        st.header("Performance Leaderboard")
        
        if st.session_state.employee_performance:
            # Convert the performance data to a DataFrame
            performance_data = list(st.session_state.employee_performance.values())
            perf_df = pd.DataFrame(performance_data)
            
            # Create a scoring system
            perf_df['performance_score'] = (
                (perf_df['tasks_completed'] * 10) + 
                (perf_df['high_priority_completed'] * 5) + 
                (perf_df['medium_priority_completed'] * 3) + 
                (perf_df['low_priority_completed'] * 1) -
                (perf_df['avg_completion_time'] * 2) +
                (perf_df['on_time_completion_rate'] * 0.5)
            )
            
            # Sort by performance score (descending)
            perf_df = perf_df.sort_values('performance_score', ascending=False)
            
            # Add rank column
            perf_df['rank'] = range(1, len(perf_df) + 1)
            
            # Format for display
            display_cols = [
                'rank', 'employee_name', 'tasks_completed', 
                'high_priority_completed', 'medium_priority_completed', 'low_priority_completed',
                'avg_completion_time', 'on_time_completion_rate', 'performance_score'
            ]
            
            display_df = perf_df[display_cols].copy()
            
            # Rename columns for display
            display_df.columns = [
                'Rank', 'Employee', 'Tasks Completed', 
                'High Priority', 'Medium Priority', 'Low Priority',
                'Avg. Completion Time (days)', 'On-time Rate (%)', 'Performance Score'
            ]
            
            # Round numeric columns
            display_df['Avg. Completion Time (days)'] = display_df['Avg. Completion Time (days)'].round(2)
            display_df['On-time Rate (%)'] = display_df['On-time Rate (%)'].round(1)
            display_df['Performance Score'] = display_df['Performance Score'].round(1)
            
            # Display top performers with highlighting
            st.subheader("Employee Rankings")
            st.write("Employees are ranked based on a performance score that considers task completion, task priority, completion time, and timeliness.")
            
            # Function to highlight top performers
            def highlight_top_ranks(s):
                is_rank = s.name == 'Rank'
                return ['background-color: gold' if is_rank and val == 1
                        else 'background-color: silver' if is_rank and val == 2
                        else 'background-color: #cd7f32' if is_rank and val == 3
                        else '' for val in s]
            
            st.dataframe(display_df.style.apply(highlight_top_ranks))
            
            # Display performance insights
            st.subheader("Performance Insights")
            
            # Top performer
            if not perf_df.empty:
                top_performer = perf_df.iloc[0]
                st.write(f"🏆 **Top Performer:** {top_performer['employee_name']} with {top_performer['tasks_completed']} tasks completed")
                
                # Most improved (could be based on recent activity)
                st.write("### Promotion Recommendations")
                st.write("Based on the performance metrics, the following employees might be considered for promotion:")
                
                for i, row in perf_df.head(3).iterrows():
                    if row['tasks_completed'] >= 5 and row['on_time_completion_rate'] >= 80:
                        st.write(f"✅ **{row['employee_name']}** - Completed {row['tasks_completed']} tasks with a {row['on_time_completion_rate']:.1f}% on-time rate")
        else:
            st.info("No performance data available yet. Complete some tasks to see the leaderboard.")
    
    # Add a footer
    st.markdown("---")
    st.caption("AI Employee Task Assignment System | Developed with Streamlit")
else:
    st.info("Please upload the employee_positions_dataset.csv file to continue.")
