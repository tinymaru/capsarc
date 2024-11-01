from flask import render_template, request, jsonify, session, redirect, url_for, flash
from authentication import get_user_id_from_username, get_user_saved_project_ids, change_password
from connect import get_database_connection
import os

# Function to fetch current user's details including profile picture
def get_current_user():
    username = session.get('username')
    if not username:
        return None
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user and 'profile_picture_url' in user and user['profile_picture_url']:
            user['profile_picture'] = url_for('static', filename=user['profile_picture_url'])
        else:
            user['profile_picture'] = url_for('static', filename='images/default_profile_picture.jpg')
    finally:
        cursor.close()
        conn.close()
    return user

# home.html: Function to get projects based on year
def get_projects(year=2023, results_per_page=10, page=1):
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT * FROM project_details WHERE Publication_Year = %s"
        cursor.execute(query, (year,))
        projects = cursor.fetchall()
        
        total_results = len(projects)
        start = (page - 1) * results_per_page
        end = start + results_per_page
        paginated_projects = projects[start:end]
    finally:
        cursor.close()
        conn.close()

    return paginated_projects, total_results

# home.html: Search Bar with dropdown suggestion (Title)
def search_projects(query):
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        search_query = f"%{query}%"
        cursor.execute("SELECT title as Title FROM project_details WHERE Title LIKE %s", (search_query,))
        suggestions = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return suggestions

# project_details.html: Display the projects details of a capstone project once the link title is clicked.
def get_project_details(identifier):
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        try:
            project_id = int(identifier)
            cursor.execute("SELECT * FROM project_details WHERE project_id = %s", (project_id,))
        except ValueError:
            cursor.execute("SELECT * FROM project_details WHERE Title = %s", (identifier,))
        project = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return project


# Function to get filtered projects based on search criteria
def get_filtered_projects(query=None, year_from=None, year_to=None, major=None, abstract=None, results_per_page=10, page=1):
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        base_query = "SELECT * FROM project_details WHERE 1=1"
        params = []

        if query:
            base_query += " AND (Title LIKE %s OR Authors LIKE %s OR Keywords LIKE %s)"
            params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
        if year_from:
            base_query += " AND Publication_Year >= %s"
            params.append(year_from)
        if year_to:
            base_query += " AND Publication_Year <= %s"
            params.append(year_to)
        if major:
            base_query += " AND Major = %s"
            params.append(major)
        if abstract:
            base_query += " AND Abstract LIKE %s"
            params.append(f"%{abstract}%")
        
        cursor.execute(base_query, params)
        results = cursor.fetchall()
        
        total_results = len(results)
        start = (page - 1) * results_per_page
        end = start + results_per_page
        paginated_results = results[start:end]
    finally:
        cursor.close()
        conn.close()
    
    return paginated_results, total_results

# Function to save project details to user's library, avoiding duplication
def save_project_to_library(project_id):
    if 'username' in session:
        user_id = get_user_id_from_username(session['username'])
        if user_id:
            conn = get_database_connection()
            cursor = conn.cursor()
            try:
                # Check if the project is already saved
                cursor.execute("SELECT COUNT(*) FROM user_library WHERE user_id = %s AND project_id = %s", (user_id, project_id))
                already_saved = cursor.fetchone()[0] > 0
                
                if not already_saved:
                    # If not saved, insert into user_library
                    cursor.execute("INSERT INTO user_library (user_id, project_id) VALUES (%s, %s)", (user_id, project_id))
                    conn.commit()
                
                # No JSON response upon successful save, return saved and already_saved status
                return True, already_saved
            except Exception as e:
                print(f"Error saving project: {e}")
                conn.rollback()
                # No JSON response upon failure
                return False, False
            finally:
                cursor.close()
                conn.close()
    # User not logged in response
    return False, False



# Function to get user-specific saved projects with pagination
def get_user_projects(user_id, results_per_page=10, page=1):
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) as total FROM user_library WHERE user_id = %s", (user_id,))
        total_results = cursor.fetchone()['total']
        
        start = (page - 1) * results_per_page
        query = """
            SELECT ul.lib_id, ul.timestamp, pd.* 
            FROM user_library ul 
            JOIN project_details pd ON ul.project_id = pd.project_id 
            WHERE ul.user_id = %s 
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (user_id, results_per_page, start))
        projects = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return projects, total_results

# Function to delete a saved project from user's library
def delete_project_from_library(entry_id):
    if 'username' in session:
        user_id = get_user_id_from_username(session['username'])
        if user_id:
            conn = get_database_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM user_library WHERE lib_id = %s AND user_id = %s", (entry_id, user_id))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error deleting project: {e}")
                conn.rollback()
                return False
            finally:
                cursor.close()
                conn.close()
    return False




#ROUTES
def index():
    return render_template('index.html')

# home.html
def home():
    results_per_page = int(request.args.get('results_per_page', 10))
    page = int(request.args.get('page', 1))

    projects, total_results = get_projects(year=2023, results_per_page=results_per_page, page=page)

    # Determine which projects are saved by the current user
    if 'username' in session:
        user_id = get_user_id_from_username(session['username'])
        if user_id:
            saved_project_ids = get_user_saved_project_ids(user_id)
            for project in projects:
                project['is_saved'] = project['project_id'] in saved_project_ids
        else:
            for project in projects:
                project['is_saved'] = False
    else:
        for project in projects:
            project['is_saved'] = False
    
    total_pages = (total_results + results_per_page - 1) // results_per_page

    return render_template('home.html', projects=projects, total_pages=total_pages, current_page=page, results_per_page=results_per_page)

def search():
    query = request.args.get('query')
    suggestions = search_projects(query)
    return jsonify(suggestions)

# project_details.html
def project_details(identifier):
    project = get_project_details(identifier)
    
    if project:
        # Determine if the project is saved by the current user
        if 'username' in session:
            user_id = get_user_id_from_username(session['username'])
            if user_id:
                saved_project_ids = get_user_saved_project_ids(user_id)
                project['is_saved'] = project['project_id'] in saved_project_ids
            else:
                project['is_saved'] = False
        else:
            project['is_saved'] = False

        # Generate the URL to view the PDF
        pdf_url = url_for('view_pdf', identifier=identifier)  # Pass project ID, not pdf_file

        # Pass the pdf_url to the template
        return render_template('project_details.html', project=project, pdf_url=pdf_url)
    else:
        return "Project not found", 404

    
# browse.html route
def browse():
    query = request.args.get('query')
    year_from = request.args.get('Publication_Year_From')
    year_to = request.args.get('Publication_Year_To')
    major = request.args.get('Major')
    abstract = request.args.get('Abstract')
    results_per_page = int(request.args.get('results_per_page', 10))
    page = int(request.args.get('page', 1))

    # Fetch filtered projects
    projects, total_results = get_filtered_projects(
         query=query, year_from=year_from, year_to=year_to, major=major,
        results_per_page=results_per_page, page=page
    )
    
    # Determine which projects are saved by the current user
    if 'username' in session:
        user_id = get_user_id_from_username(session['username'])
        if user_id:
            saved_project_ids = get_user_saved_project_ids(user_id)
            for project in projects:
                project['is_saved'] = project['project_id'] in saved_project_ids
        else:
            for project in projects:
                project['is_saved'] = False
    else:
        for project in projects:
            project['is_saved'] = False

    total_pages = (total_results + results_per_page - 1) // results_per_page

    return render_template('browse.html', projects=projects, total_pages=total_pages, current_page=page, results_per_page=results_per_page)


# about.html
def about():
    return render_template('about.html')

# about.html
def about_us():
    return render_template('about_us.html')

def save_project():
    if 'username' in session:
        project_id = request.json.get('project_id')
        if project_id:
            saved, already_saved = save_project_to_library(project_id)
            if saved:
                return jsonify({'saved': True, 'already_saved': already_saved}), 200
            else:
                return jsonify({'saved': False}), 200
    return jsonify({'error': 'Unauthorized'}), 401

# Route to handle deleting a saved project
def delete_project():
    if 'username' in session:
        entry_id = request.json.get('entry_id')
        if entry_id:
            deleted = delete_project_from_library(entry_id)
            if deleted:
                return '', 204
    return '', 400

# Example route to display saved searches with pagination
def user_library():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = get_user_id_from_username(session['username'])
    if not user_id:
        return redirect(url_for('login'))

    results_per_page = int(request.args.get('results_per_page', 10))
    page = int(request.args.get('page', 1))
    
    saved_projects, total_results = get_user_projects(user_id, results_per_page, page)
    total_pages = (total_results + results_per_page - 1) // results_per_page

    return render_template('user_library.html', saved_projects=saved_projects, total_pages=total_pages, current_page=page, results_per_page=results_per_page)

def user_profile():
    user = get_current_user()
    if not user:
        flash('Please log in to access your profile.')
        return redirect(url_for('login'))
    return render_template('user_profile.html', user=user)

# change_password.html
def change_password_route():
    return change_password()

def basename_filter(file_path):
    """Extracts the basename from a file path."""
    return os.path.basename(file_path)

def reset_password_request():
    return render_template('reset_password_request.html')
