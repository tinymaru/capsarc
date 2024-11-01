from flask import render_template, flash, request, redirect, url_for, jsonify, send_file, abort, session
from connect import get_database_connection
from user import get_project_details
from pdf import PDFConfig
import io
import google.generativeai as genai
import fitz
import bcrypt
from datetime import datetime
from google.oauth2 import service_account
import google.auth


credentials_info = {
  "type": "service_account",
  "project_id": "imrad-generator-438711",
  "private_key_id": "78866a83ef2843f60dfce7f21048864722202df2",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDPNWhG/OuT7eIk\nWzD1w8paGrrgjzWnMC1InPeRDV/FNLIAtTXABRxV8vt5cXE7PMJmNAOHxQKLhaRG\n1BGLIK7019lq3WrCpX/7GGCKHBnTBcWZb+lhx+f389deQ+2E999wO1jH4GzIhJis\nJXUrJDe2jIFNmVwxdEy4VrdjvOLU9OEFEy1YRE1TmuAV48PUW5ljj87r6bRQ2LMP\nWFl4WjKADOF6p3UWzGzs8VYfRqgawSY0w3U9SNo1xKsgX9JMV1mvPyV1V8w2kiSX\n9iGOkkoNOemUCF6aMAkW3BBHJpO2vWdCzyogys35LeVhf8v6hVe+dFt64kl0dO8z\n7xRgHZ1bAgMBAAECggEAAwGtl7z0LdRiltksLFXhAyCvu+jVxBsNEJYpVbn4mGq5\nZQzOWhD9fTF9KnxxQoUjY4quGG8D3132aS6vj1Zz/tzGo1XRj62by9sgn3mJnz7g\nscLCA4L8RFHXFl+RPBIvPW9LlY7e3lrTU23WSAkvSFYqAdrh4e6s/7wGYQt18R7u\nFU40rUrPcrgq4gqeuKJAqEF+mKe1X+KkVzix9v/ez3GYiJ99SN7S826rN5sQyhXK\n/1G/EoA/rs7X3C4z0BUcYfDRRnXHwh2SYUwMd1wtTCumMoSKq2uM7XYOGAfRCqp1\n2J0hzszU2t1sr2gwO8v8YYrUQTeNFDPnB69ix2gwQQKBgQD3MtLFHxQ3m0d+FP21\n/Hs6PnzD5o/5+KAg2JgJBnJptFISPRRA92jSxXhtOrMMUK+Ur6sT4evV58HAniYP\nuXmIlCE0dtReaPWuNrTgR4Rn2fU70Gw54AzzzUGWq140jbycRirJrV083z9JBjow\nosaLK/K9TXzxu7F+yEIfzlCIwQKBgQDWlhUHzt9QjcJiqKKffqjRE4jrj1XCOPz1\nAzAQOWpiKUlS+rpIgUaJfYKyF6GY5x8Gp2liWRDH3vR8vcgATNC7JsEo0bGxjpDF\nrbEArB+b63EdZy/oqjuaY8d537mLszQmtcTHsTGMfbb3gqsZjH1t4SfGgg6iiEqT\n7s3FL8JxGwKBgQCpUQVvAVeestwoLwaMlVBuV4irwgvR4wsDFHgmjmTlpB4m4fEy\ngoQpAhr3biJfiBCLnjtm1fLsQ97BKVHWqWrmMtf/kHjr5aaJ2mzPxgyZ+X9wpdTL\nW3xjra6EHgLbqk2LGMCL/RQE8sDtKrfGwmeNwd907FNtW+s6dL5d/LnKwQKBgQC2\nB7ZrWzfgs4BUBM1/EwjN4w5hFMQg8ArVJREekjYGcxN6Sqq/WrqlY0z9GkLA3D5b\nfKRPA1LS2fT35F3Gs2LVf7iXkdp0zoVMy1y9P0XJFF5uHNxtOAs7mqzaW8igEzKI\nK+VzqIJptTMCn1vZXm4ASeFd6XHUulzZRNhVD4CYRQKBgQDQSPX/0W9OCQ+LwXCV\ns/M7rxg+OwXtFz87g60Src4Re6cUdyROfDpRJk6zw/0NQXbJ4IBofhR+5gLHmigX\nms4EWgjRh40P0dXjuD+aNwUo2XUK/uwCSeevGY+diUOPdxGCU2LaTHIO+UlxWZ48\nxYp1E7MFx5V3LRMdVZl29lL1nA==\n-----END PRIVATE KEY-----\n",
  "client_email": "imrad-generator@imrad-generator-438711.iam.gserviceaccount.com",
  "client_id": "106169919050706557401",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/imrad-generator%40imrad-generator-438711.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

credentials = service_account.Credentials.from_service_account_info(credentials_info)

location = "us-central1"
model = genai.GenerativeModel("gemini-1.5-flash-002")


def update_last_active():
    conn = get_database_connection()
    cursor = conn.cursor()

    # Update last_active for active users where it is NULL
    cursor.execute("UPDATE users SET last_active = NOW() WHERE last_active IS NULL AND status = 'active'")
    conn.commit()

    cursor.close()
    conn.close()

    return "Last active timestamps updated for active users.", 200

def admin_index():
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute('SELECT COUNT(*) FROM project_details;')
        count_projects = cursor.fetchone()['COUNT(*)']

        cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'active';")
        count_active_users = cursor.fetchone()['COUNT(*)']

        cursor.execute('SELECT COUNT(*) FROM users;')
        count_users = cursor.fetchone()['COUNT(*)']

        cursor.execute('''
            SELECT 
                project_details.project_id, 
                project_details.Title, 
                project_details.Authors, 
                project_details.Major, 
                project_details.Publication_Year, 
                COUNT(user_library.project_id) AS save_count
            FROM user_library
            JOIN project_details ON user_library.project_id = project_details.project_id
            GROUP BY project_details.project_id
            ORDER BY save_count DESC;
        ''')
        projects = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    
    return render_template('admin_index.html', count_projects=count_projects, count_active_users=count_active_users, count_users=count_users, projects=projects)


def admin_view_project(project_id):
    project = get_project_details(project_id)
    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('capstone_projects'))
        
    # Generate the URL to view the PDF
    pdf_url = url_for('view_pdf', identifier=project_id)

    return render_template('admin_view_project.html', project=project, pdf_url=pdf_url)

def view_pdf(identifier):
    project = get_project_details(identifier)
    
    if project and project['pdf_file']:
        pdf_data = project['pdf_file']  # Binary data of the PDF
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=False,  # Do not prompt for download
            download_name=f"{identifier}.pdf"  # Use download_name instead of attachment_filename
        )
    else:
        abort(404, description="PDF file not found.")
    
def capstone_projects():
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM project_details;')
    projects = cursor.fetchall()
  
    return render_template('capstone_projects.html', projects=projects)

def update_last_active():
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_database_connection()
        cursor = conn.cursor()

        # Update the last_active field for the current user
        cursor.execute("UPDATE users SET last_active = %s WHERE user_id = %s", 
                       (datetime.now(), user_id))
        conn.commit()

        cursor.close()
        conn.close()

def active_users():
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)

    # Query to get active users with their last active timestamp
    cursor.execute("SELECT * FROM users WHERE status = 'active' ORDER BY last_active DESC")
    active_users = cursor.fetchall()

    cursor.close()
    conn.close()

    # Pass the active users data to the template
    return render_template('active_users.html', active_users=active_users)


def users():
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM users;')
    users = cursor.fetchall()
  
    return render_template('users.html', users=users)

def reset_password(user_id):
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch the specific user by user_id
    cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
    users = cursor.fetchone()

    if not users:
        flash('User not found.', 'danger')
        return redirect(url_for('users'))

    if request.method == 'POST':
        new_password = request.form['new_password']

        # Hash the password with bcrypt
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        # Update the user's password in the database
        cursor.execute('UPDATE users SET password_hash = %s WHERE user_id = %s', (hashed_password, user_id))
        conn.commit()

        flash('Password reset successfully.', 'info')
    return render_template('reset_password.html', users=users)

def delete_capstone_project():
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)
    project_id = request.form['project_id']

    try:
        cursor.execute("DELETE FROM project_details WHERE project_id = %s", (project_id,))
        conn.commit()
        cursor.close()
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

def delete_user():
    conn = get_database_connection()
    cursor = conn.cursor(dictionary=True)
    user_id = request.form['user_id']

    try:
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()
        cursor.close()
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Route for uploading projects
def upload_project():
    conn = get_database_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        # Check for uploaded file
        if "pdf" not in request.files:
            return "No file part"
        file = request.files["pdf"]
        if file.filename == "":
            return "No selected file"

        # Get form data
        title = request.form["title"]
        authors = request.form["authors"]
        major = request.form["major"]
        year = request.form["year"]
        keywords = request.form["keywords"]
        abstract = request.form["abstract"]

        query = """
        SELECT COUNT(*) FROM project_details
        WHERE Title = %s AND Authors = %s AND Publication_Year = %s AND Keywords = %s AND Abstract = %s
        """
        cursor.execute(query, (title, authors, year, keywords, abstract))
        project_exists = cursor.fetchone()[0]

        if project_exists:
            flash("Project already exists", 'danger')
            return redirect(request.url)


        # Extract text from the uploaded PDF
        text = extract_text_from_pdf(file)

        # Save the capstone project details and PDF to the database
        save_result = save_pdf_to_db(title, authors, major, year, keywords, abstract, file)
        if save_result != "Success":
            return save_result

        # Generate the IMRaD format using a single prompt
        imrad_response = generate_imrad(text)

        # Save IMRaD format and text with line spacing to the database
        save_imrad_result = save_generated_imrad_and_spacing(title, imrad_response)
        if save_imrad_result != "Success":
            return save_imrad_result

        return render_template(
            "upload_project.html",
            message="Project uploaded successfully!"
        )

    return render_template("upload_project.html")



def extract_text_from_pdf(file):
    try:
        pdf_document = fitz.open(stream=file.read(), filetype="pdf")
        full_text = ""

        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            full_text += page.get_text()

        return full_text
    
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def generate_imrad(text):
    # Use a single prompt to generate the IMRaD format
    prompt = "Summarize the PDF in IMRaD(Introduction, Method, Results, and Discussion) format. Make it in only 4 paragraphs and make each paragraph long and don't include words like 'Introduction', 'Method', 'Results', and 'Discussion'. Make each paragraph long."
    response = model.generate_content(f"{prompt}: {text}")
    
    return response.text

def save_generated_imrad_and_spacing(title, imrad_text):
    try:
        # Replace line breaks with <br> tags for proper HTML rendering
        imrad_with_spacing = imrad_text.replace("\n", "<br>")

        connection = get_database_connection()
        if connection is None:
            return "Database connection failed"
        
        cursor = connection.cursor()

        # Update the project details to include the generated IMRaD with HTML line breaks
        query = """
        UPDATE project_details 
        SET generated_imrad = %s 
        WHERE Title = %s
        """
        cursor.execute(query, (imrad_with_spacing, title))

        connection.commit()
        cursor.close()
        connection.close()

        return "Success"
    
    except Exception as e:
        return f"Error saving IMRaD to database: {str(e)}"


def save_pdf_to_db(title, authors, major, year, keywords, abstract, file):
    try:
        connection = get_database_connection()
        if connection is None:
            return "Database connection failed"

        cursor = connection.cursor()

        file.seek(0)
        file_data = file.read()

        query = """
        INSERT INTO project_details (Title, Authors, Publication_Year, Major, Keywords, Abstract, pdf_file) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (title, authors, year, major, keywords, abstract, file_data))

        connection.commit()
        cursor.close()
        connection.close()
        
        return "Success"
    
    except Exception as e:
        return f"Error saving PDF to database: {str(e)}"

    
# Route for editing a project
def edit_project(project_id):
    project = get_project_details(project_id)  # Fetch the project details from the database using the ID
    conn = get_database_connection()
    cursor = conn.cursor()

    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('capstone_projects'))

    if request.method == 'POST':
        # Collect updated project details from the form
        title = request.form.get('title')
        authors = request.form.get('authors')
        major = request.form.get('major')
        year = request.form.get('year')
        keywords = request.form.get('keywords')
        abstract = request.form.get('abstract')

        # Default to the existing PDF file if no new file is uploaded
        pdf_data = project.get('pdf_file', b'')

        # Check if the project already exists
        query = """
        SELECT COUNT(*) FROM project_details
        WHERE Title = %s AND Authors = %s AND Publication_Year = %s AND Keywords = %s AND Abstract = %s
        """
        cursor.execute(query, (title, authors, year, keywords, abstract))
        project_exists = cursor.fetchone()[0]

        if project_exists:
            flash("Project already exists", 'danger')
            return redirect(request.url)

        # Check if a new file is uploaded
        if 'pdf' in request.files:
            file = request.files['pdf']
            if file.filename != '':
                if PDFConfig.allowed_upload_file(file.filename):
                    pdf_data = file.read()  # Read the new PDF file content
                else:
                    flash('Invalid file type.', 'danger')
                    return redirect(request.url)

        # Update the project details in the database
        success = update_project_details({
            'project_id': project_id,
            'pdf_file': pdf_data,
            'Title': title,
            'Authors': authors,
            'Major': major,
            'Publication_Year': year,
            'Keywords': keywords,
            'Abstract': abstract
        })

        if success:
            flash('Project details updated successfully!', 'info')
            return redirect(url_for('admin_view_project', project_id=project_id))
        else:
            flash('Failed to update project details. Please try again.', 'danger')

    cursor.close()
    conn.close()
    
    # Ensure Publication_Year is available
    year = project.get('Publication_Year', None)

    # Generate a range of years (you can adjust this range as needed)
    year_options = list(range(2021, 2024))

    return render_template('edit_project.html', project=project, year=year, year_options=year_options)


def update_project_details(project_details):
    conn = get_database_connection()
    cursor = conn.cursor()

    try:
        # Update query to modify the project details in the database
        sql = '''UPDATE project_details
                 SET pdf_file = %s,
                     Title = %s,
                     Authors = %s,
                     Publication_Year = %s,
                     Major = %s,
                     Keywords = %s,
                     Abstract = %s
                 WHERE project_id = %s'''
        
        # Execute the query with provided details
        cursor.execute(sql, (
            project_details['pdf_file'],
            project_details['Title'],
            project_details['Authors'],
            project_details['Publication_Year'],
            project_details['Major'],
            project_details['Keywords'],
            project_details['Abstract'],
            project_details['project_id']
        ))
        
        # Commit the changes
        conn.commit()
        
        return True  # Indicate success
    except Exception as e:
        # Log the error (optional) and handle it
        print(f"Error updating project details: {e}")
        conn.rollback()
        return False  # Indicate failure
    finally:
        cursor.close()
        conn.close()
