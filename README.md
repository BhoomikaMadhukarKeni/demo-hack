<<<<<<< HEAD
# demo-hack
=======
# AI Employee Task Assignment System

An AI-powered system for optimal task allocation among employees based on skills, availability, and performance metrics.

## Features

- **Intelligent Task Matching**: Automatically matches tasks to the most suitable employees based on required skills, current availability, and historical preferences
- **Employee Status Tracking**: Real-time monitoring of employee availability with color-coded indicators (🟢Free, 🟡Partially Working, 🔴Fully Occupied, ✅Completed)
- **Performance Analytics**: Tracks employee performance metrics including task completion rates, priority handling, and on-time delivery
- **Preference Learning**: Learns from past task assignments to improve future matching based on employee performance and preferences
- **Task Progress Monitoring**: Allows tracking task completion percentage and self-acknowledgment capabilities
- **Task Reassignment**: Enables managers to reassign incomplete tasks when necessary

## System Components

1. **Employee Manager**: Handles employee data, skills tracking, and availability status
2. **Task Matcher**: Performs intelligent task-to-employee matching considering multiple factors
3. **Performance Tracking**: Monitors and analyzes employee performance metrics
4. **Streamlit Interface**: Provides an intuitive web interface for all system features

## Technical Implementation

- Python-based backend with Streamlit web interface
- Pandas for data management
- Scikit-learn for text similarity analysis and preference learning
- CSV-based data storage with real-time updates

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `streamlit run app.py`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built as a hackathon prototype to solve real-world company task allocation challenges
- Special thanks to all contributors
>>>>>>> aa038d6 (Update employee database and Streamlit configuration.)
