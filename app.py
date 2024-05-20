from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from datetime import datetime
import pandas as pd
import os

app = Flask(__name__)

# Define a directory to store temporary files
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Dictionary to store attendance records where keys are dates
attendance_records_by_date = {}

# Function to record check-in time
def record_check_in(employee_name, check_in_time):
    date = check_in_time.date()
    if date not in attendance_records_by_date:
        attendance_records_by_date[date] = []
    attendance_records_by_date[date].append({'employee_name': employee_name, 'check_in': check_in_time})

# Function to record check-out time
def record_check_out(employee_name, check_out_time):
    date = check_out_time.date()
    if date in attendance_records_by_date:
        for record in attendance_records_by_date[date]:
            if record['employee_name'] == employee_name and 'check_out' not in record:
                record['check_out'] = check_out_time
                break

# Route for index page
@app.route('/')
def index():
    return render_template('index.html')

# Route for handling check-in/check-out form submission
@app.route('/record_action', methods=['POST'])
def record_action():
    datetime_str = request.form['datetime']
    employee_name = request.form['employee_name']  # Change to employee_name
    action = request.form['action']

    # Convert datetime string to datetime object
    check_time = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')

    # Record check-in or check-out based on action
    if action == 'check_in':
        record_check_in(employee_name, check_time)  # Pass employee_name
    elif action == 'check_out':
        record_check_out(employee_name, check_time)  # Pass employee_name

    return redirect(url_for('index'))


# Function to calculate hours worked
def calculate_hours_worked(check_in_time, check_out_time):
    if check_out_time is None:
        return 0  # If no check-out time is recorded, assume 0 hours worked
    else:
        # Calculate the difference in hours between check-out and check-in times
        time_difference = check_out_time - check_in_time
        hours_worked = time_difference.total_seconds() / 3600  # Convert seconds to hours
        return hours_worked

# Route for viewing attendance records
@app.route('/attendance')
def view_attendance():
    # Calculate hours worked for each record
    for date, records in attendance_records_by_date.items():
        for record in records:
            check_in_time = record.get('check_in')
            check_out_time = record.get('check_out')
            record['hours_worked'] = calculate_hours_worked(check_in_time, check_out_time)

    return render_template('attendance.html', attendance_records_by_date=attendance_records_by_date)

# Function to calculate hours worked
def calculate_hours_worked(check_in_time, check_out_time):
    if check_out_time is None or check_in_time is None:
        return "N/A"  # If no check-in or check-out time is recorded, show N/A
    else:
        # Calculate the difference in hours between check-out and check-in times
        time_difference = check_out_time - check_in_time
        hours_worked = time_difference.total_seconds() / 3600  # Convert seconds to hours
        return "{:.2f}".format(hours_worked)  # Format hours worked to 2 decimal places


# Route for downloading attendance records as Excel file
@app.route('/download_attendance')
def download_attendance():
    try:
        # Initialize lists to store data
        dates = []
        employee_names = []
        check_ins = []
        check_outs = []
        hours_worked = []

        # Append data to lists
        for date, records in attendance_records_by_date.items():
            for record in records:
                dates.append(date)
                employee_names.append(record['employee_name'])
                check_ins.append(record.get('check_in', 'Not checked in'))
                check_outs.append(record.get('check_out', 'Not checked out'))
                hours_worked.append(calculate_hours_worked(record.get('check_in'), record.get('check_out')))

        # Create DataFrame from lists
        df = pd.DataFrame({
            'Date': dates,
            'Employee Name': employee_names,
            'Check In': check_ins,
            'Check Out': check_outs,
            'Hours Worked': hours_worked
        })

        # Save DataFrame as Excel file
        excel_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'attendance_records.xlsx')
        df.to_excel(excel_filename, index=False)

        # Return the Excel file as a downloadable attachment
        return send_from_directory(directory=app.config['UPLOAD_FOLDER'], path='attendance_records.xlsx', as_attachment=True)

    except Exception as e:
        return f"An error occurred: {str(e)}"

# Run the Flask application
if __name__ == "__main__":
    app.run(debug=True)
