from flask import Flask, render_template_string, request, redirect, url_for, session
import random
import sqlite3
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.secret_key = 'fu_info_tech_secret_key'

ADMIN_IDENTIFIER = "tanvir.hassan7242@gmail.com"
ADMIN_PASSWORD = "T@nv1r#2022"

# Bangladesh Time Zone (UTC+6)
BD_TIMEZONE = timezone(timedelta(hours=6))

def get_bd_time_string():
    return datetime.now(BD_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')

def init_db():
    conn = sqlite3.connect('fu_infotech.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            designation TEXT NOT NULL,
            operator TEXT NOT NULL,
            balance INTEGER DEFAULT 0,
            used INTEGER DEFAULT 0,
            created_date TEXT DEFAULT ''
        )
    ''')
    try:
        cursor.execute("ALTER TABLE employees ADD COLUMN created_date TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requisitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_name TEXT NOT NULL,
            type TEXT NOT NULL,
            details TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            timestamp TEXT DEFAULT ''
        )
    ''')
    conn.commit()
    conn.close()

init_db()

otp_storage = {}

BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 0; color: #333; }
        .top-header { background: #ffffff; height: 65px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; padding: 0 25px; position: fixed; top: 0; left: 0; right: 0; z-index: 1000; }
        .brand-container { display: flex; align-items: center; gap: 12px; }
        .brand-logo { height: 35px; object-fit: contain; }
        .brand-title { font-size: 20px; font-weight: bold; color: #1e293b; position: absolute; left: 50%; transform: translateX(-50%); }
        .brand-title span { color: #3b82f6; }
        .user-profile-area { position: relative; display: flex; align-items: center; gap: 12px; cursor: pointer; user-select: none; }
        .user-avatar { width: 40px; height: 40px; background: #1e293b; color: #ffffff; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 16px; overflow: hidden; }
        .user-avatar img { width: 100%; height: 100%; object-fit: cover; }
        .user-meta { display: flex; flex-direction: column; text-align: right; }
        .user-name-display { font-size: 14px; font-weight: bold; color: #1e293b; display: flex; align-items: center; gap: 6px; justify-content: flex-end; }
        .user-id-display { font-size: 12px; color: #64748b; font-weight: 600; }
        .profile-dropdown { display: none; position: absolute; top: 50px; right: 0; background: #ffffff; min-width: 230px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; z-index: 1001; }
        .profile-dropdown.show { display: block; }
        .dropdown-header-info { padding: 15px; background: #1e293b; color: white; border-bottom: 1px solid #334155; }
        .profile-dropdown a { display: flex; align-items: center; gap: 12px; padding: 12px 16px; color: #334155; text-decoration: none; font-size: 14px; transition: background 0.2s; }
        .profile-dropdown a:hover { background-color: #f1f5f9; }
        .profile-dropdown a.logout-btn { color: #dc2626; border-top: 1px solid #e2e8f0; }
        .app-layout { display: flex; margin-top: 65px; min-height: calc(100vh - 65px); }
        .sidebar { width: 260px; background: #1e293b; color: #cbd5e1; padding-top: 20px; position: fixed; height: calc(100vh - 65px); overflow-y: auto; }
        .sidebar a { display: block; color: #cbd5e1; text-decoration: none; padding: 12px 20px; font-size: 14px; border-left: 4px solid transparent; transition: all 0.3s; margin-top: 5px; }
        .sidebar a:hover, .sidebar a.active { background: #334155; color: #ffffff; border-left-color: #3b82f6; }
        .main-content { margin-left: 260px; padding: 30px; width: calc(100% - 260px); background: #f4f6f9; }
        .cards-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 25px; }
        .card { background: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
        .card h3 { margin: 0 0 10px 0; font-size: 14px; color: #64748b; }
        .card .value { font-size: 24px; font-weight: bold; color: #1e293b; }
        .panel { background: #ffffff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; margin-bottom: 25px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border-bottom: 1px solid #e2e8f0; padding: 12px 10px; text-align: left; font-size: 14px; }
        th { background-color: #f8fafc; color: #475569; font-weight: 600; }
        input, select { padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; width: 100%; box-sizing: border-box; margin-top: 5px; }
        input.invalid-field { border: 2px solid #dc2626 !important; background-color: #fef2f2; }
        button { background-color: #3b82f6; color: white; padding: 8px 16px; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; transition: background 0.3s; }
        button:hover { background-color: #2563eb; }
        .badge { padding: 3px 8px; border-radius: 12px; font-size: 10px; font-weight: bold; }
        .badge-admin { background: #fee2e2; color: #dc2626; }
        .badge-member { background: #dcfce7; color: #16a34a; }
        .badge-pending { background: #fef3c7; color: #d97706; }
        .badge-approved { background: #dcfce7; color: #16a34a; }
        .badge-rejected { background: #fee2e2; color: #dc2626; }
        .login-body { display: flex; justify-content: center; align-items: center; height: 100vh; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); margin: 0; }
        .login-card { background: white; padding: 40px; border-radius: 12px; width: 100%; max-width: 400px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); text-align: center; }
        .error { color: #dc2626; font-size: 13px; margin-bottom: 15px; }
        .success { background: #dcfce7; color: #16a34a; padding: 10px; border-radius: 6px; margin-bottom: 15px; font-size: 14px; }
        
        /* Classic & Premium 3-dot Dropdown Menu Style */
        .dropdown { position: relative; display: inline-block; }
        .dropbtn { background: #f8fafc; color: #475569; width: 32px; height: 32px; font-size: 16px; border: 1px solid #e2e8f0; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s ease; }
        .dropbtn:hover { background: #f1f5f9; color: #1e293b; border-color: #cbd5e1; }
        .dropdown-content { display: none; position: absolute; right: 0; top: 38px; background-color: #ffffff; min-width: 145px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1); z-index: 20; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; padding: 6px; animation: dropdownFade 0.2s ease; }
        @keyframes dropdownFade { from { opacity: 0; transform: translateY(-5px); } to { opacity: 1; transform: translateY(0); } }
        .dropdown-content a { color: #334155; padding: 8px 12px; text-decoration: none; display: flex; align-items: center; gap: 10px; font-size: 13px; font-weight: 500; border-radius: 5px; transition: background 0.15s ease, color 0.15s ease; }
        .dropdown-content a:hover { background-color: #f8fafc; color: #3b82f6; }
        .dropdown-content a.delete-item { color: #dc2626; }
        .dropdown-content a.delete-item:hover { background-color: #fee2e2; color: #b91c1c; }
        .dropdown.show .dropdown-content { display: block; }
    </style>
</head>
<body>
    {{ content | safe }}
    <script>
        function toggleProfileMenu() {
            const dropdown = document.getElementById('profileDropdown');
            if (dropdown) dropdown.classList.toggle('show');
        }
        function toggleRowDropdown(id, event) {
            event.stopPropagation();
            document.querySelectorAll('.dropdown').forEach(el => {
                if(el.id !== 'dropdown-' + id) el.classList.remove('show');
            });
            const elem = document.getElementById('dropdown-' + id);
            if(elem) elem.classList.toggle('show');
        }
        function confirmDelete(id, name) {
            Swal.fire({
                title: 'Are you sure?',
                text: "Do you want to delete member: " + name + "?",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#dc2626',
                cancelButtonColor: '#64748b',
                confirmButtonText: 'Yes, delete it!'
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = '/delete_member/' + id;
                }
            });
        }
        window.onclick = function(event) {
            if (!event.target.closest('.user-profile-area') && !event.target.closest('.dropdown')) {
                const dropdowns = document.getElementsByClassName('profile-dropdown');
                for (let i = 0; i < dropdowns.length; i++) {
                    dropdowns[i].classList.remove('show');
                }
                document.querySelectorAll('.dropdown').forEach(el => el.classList.remove('show'));
            }
        }
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '').strip()
        if identifier and password:
            if identifier.lower() == ADMIN_IDENTIFIER.lower() and password == ADMIN_PASSWORD:
                session['logged_in'] = True
                session['user'] = identifier
                session['role'] = 'Admin'
                session['name'] = 'Md Tanvir Hassan'
                session['user_id'] = 'ADMIN-7242'
                session['profile_pic'] = ''
                
                conn = sqlite3.connect('fu_infotech.db')
                conn.execute("INSERT INTO activity_logs (action, timestamp) VALUES (?, ?)", 
                             ("Admin logged in directly with password", get_bd_time_string()))
                conn.commit()
                conn.close()
                return redirect(url_for('dashboard'))
            else:
                generated_otp = str(random.randint(1000, 9999))
                otp_storage[identifier] = generated_otp
                print("\n[SYSTEM NOTIFICATION] OTP for " + identifier + " is: " + generated_otp + "\n")
                session['temp_user'] = identifier
                return redirect(url_for('verify_otp'))
        else:
            error = "Please enter both User ID/Email and Password."
            
    body_content = f'''
    <div class="login-body">
        <div class="login-card">
            <h2 style="color: #1e293b; margin-top:0;">FU INFOTECH</h2>
            <p style="color: #64748b; font-size: 14px;">Bulk Recharge & Management System</p>
            {f'<div class="error">{error}</div>' if error else ''}
            <form method="POST">
                <input type="text" name="identifier" placeholder="User ID / Email" required autocomplete="off" style="margin-bottom: 12px;">
                <input type="password" name="password" placeholder="Password" required autocomplete="off" style="margin-bottom: 15px;">
                <button type="submit" style="width: 100%; padding: 10px;">Login</button>
            </form>
        </div>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE, title="Login - Fu Info Tech", content=body_content)

@app.route('/verify', methods=['GET', 'POST'])
def verify_otp():
    temp_user = session.get('temp_user')
    if not temp_user:
        return redirect(url_for('login'))
    error = ""
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        if otp_storage.get(temp_user) == entered_otp:
            session['logged_in'] = True
            session['user'] = temp_user
            session['role'] = 'Member'
            session['name'] = 'Team Member'
            session['user_id'] = f"EMP-{random.randint(1000, 9999)}"
            session['profile_pic'] = ''
            
            conn = sqlite3.connect('fu_infotech.db')
            conn.execute("INSERT INTO activity_logs (action, timestamp) VALUES (?, ?)", 
                         ("User logged in via OTP as Member", get_bd_time_string()))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid OTP! Please try again."
            
    body_content = f'''
    <div class="login-body">
        <div class="login-card">
            <h2 style="color: #1e293b; margin-top:0;">Verify OTP</h2>
            <p style="color: #64748b; font-size: 14px;">Enter the 4-digit code sent to server</p>
            {f'<div class="error">{error}</div>' if error else ''}
            <form method="POST">
                <input type="text" name="otp" placeholder="4-digit OTP" required maxlength="4" autocomplete="off" style="margin-bottom: 15px; text-align: center; letter-spacing: 5px; font-size: 18px;">
                <button type="submit" style="width: 100%; padding: 10px;">Verify & Login</button>
            </form>
        </div>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE, title="Verify OTP", content=body_content)

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    user_id = session.get('user_id', 'ADMIN-7242')
    name = session.get('name', 'User')
    role = session.get('role', 'Member')
    user_email = session.get('user', 'user@fuinfotech.com')
    profile_pic = session.get('profile_pic', '')
    tab = request.args.get('tab', 'overview')
    msg = request.args.get('msg', '')
    
    from_date = request.args.get('from_date', '').strip()
    to_date = request.args.get('to_date', '').strip()
    
    conn = sqlite3.connect('fu_infotech.db')
    conn.row_factory = sqlite3.Row
    
    show_no_data_popup = False
    if tab == 'employees' and from_date and to_date:
        employees = conn.execute("SELECT * FROM employees WHERE created_date BETWEEN ? AND ?", (from_date, to_date)).fetchall()
        if len(employees) == 0:
            show_no_data_popup = True
    else:
        employees = conn.execute("SELECT * FROM employees").fetchall()
        
    requisitions = conn.execute("SELECT * FROM requisitions").fetchall()
    logs = conn.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT 15").fetchall()
    
    total_balance = sum(emp['balance'] for emp in employees)
    total_used = sum(emp['used'] for emp in employees)
    total_employees = len(employees)
    total_requisitions = len(requisitions)
    conn.close()
    
    avatar_html = f'<img src="{profile_pic}" alt="Profile">' if profile_pic else name[0].upper()
    brand_header_html = '''
    <div class="brand-container">
        <img src="https://i.ibb.co/3s65q52/download.png" alt="FU INFOTECH" class="brand-logo">
    </div>
    <div class="brand-title">
        FU <span>INFOTECH</span>
    </div>
    '''
    
    content_area = ""
    if tab == 'overview':
        chart_js = """
        <script>
            const ctx = document.getElementById('financeChart').getContext('2d');
            const financeChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Current Balance', 'Total Used / Recharged'],
                    datasets: [{
                        label: 'Amount in BDT (৳)',
                        data: [""" + str(total_balance) + """, """ + str(total_used) + """],
                        backgroundColor: ['rgba(22, 163, 74, 0.7)', 'rgba(59, 130, 246, 0.7)'],
                        borderColor: ['rgb(22, 163, 74)', 'rgb(59, 130, 246)'],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: { y: { beginAtZero: true } }
                }
            });
        </script>
        """

        content_area = '''
        <div class="cards-grid">
            <div class="card">
                <h3>TOTAL MEMBERS</h3>
                <div class="value">''' + str(total_employees) + '''</div>
            </div>
            <div class="card">
                <h3>TOTAL BALANCE (CURRENT)</h3>
                <div class="value" style="color: #16a34a;">৳''' + str(total_balance) + '''</div>
            </div>
            <div class="card">
                <h3>TOTAL USED / RECHARGED</h3>
                <div class="value" style="color: #3b82f6;">৳''' + str(total_used) + '''</div>
            </div>
            <div class="card">
                <h3>OFFICE REQUISITIONS</h3>
                <div class="value" style="color: #d97706;">''' + str(total_requisitions) + '''</div>
            </div>
        </div>
        
        <div class="panel">
            <h3>📊 Financial Overview: Balance vs Used Amount</h3>
            <p style="color: #64748b; margin-bottom: 20px;">Comparison chart showing available balance versus total used/recharged amount across the system.</p>
            <div style="width: 100%; max-width: 650px; margin: auto;">
                <canvas id="financeChart" height="130"></canvas>
            </div>
        </div>
        ''' + chart_js
        
    elif tab == 'employees':
        table_rows = ""
        if len(employees) == 0:
            table_rows = '<tr><td colspan="7" style="text-align: center; color: #64748b; padding: 20px;">No members available.</td></tr>'
        else:
            for emp in employees:
                created_dt = emp['created_date'] if 'created_date' in emp.keys() and emp['created_date'] else datetime.now(BD_TIMEZONE).strftime('%Y-%m-%d')
                table_rows += f'''
                    <tr>
                        <td><b>{emp['name']}</b></td>
                        <td>{emp['phone']}</td>
                        <td>{emp['designation']}</td>
                        <td>{emp['operator']}</td>
                        <td style="color: #16a34a; font-weight: bold;">৳{emp['balance']}</td>
                        <td>{created_dt}</td>
                        <td style="text-align: right;">
                            <div class="dropdown" id="dropdown-{emp['id']}">
                                <button onclick="toggleRowDropdown({emp['id']}, event)" class="dropbtn">⋮</button>
                                <div class="dropdown-content">
                                    <a href="#" onclick="openEditModal({emp['id']}, '{emp['name']}', {emp['balance']}); return false;">✏️ Edit</a>
                                    <a href="/print_member/{emp['id']}" target="_blank">🖨️ Print</a>
                                    <a href="#" onclick="confirmDelete({emp['id']}, '{emp['name']}'); return false;" class="delete-item">🗑️ Delete</a>
                                </div>
                            </div>
                        </td>
                    </tr>
                '''
            
        add_form_section = ""
        if role == "Admin":
            show_add = request.args.get('show_add') == '1'
            add_form_section = f'''
            <div id="addMemberModal" style="display: {'block' if show_add else 'none'}; background: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e2e8f0;">
                <h4 style="margin-top: 0; color: #1e293b;">+ Add New Member</h4>
                <form id="addMemberForm" action="/add_employee" method="POST" onsubmit="return validateForm()" style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr 1fr auto; gap: 10px; align-items: end;">
                    <div>
                        <label style="font-size: 12px; color: #64748b;">Name</label>
                        <input type="text" name="name" id="nameInput" placeholder="Full Name">
                    </div>
                    <div>
                        <label style="font-size: 12px; color: #64748b;">Phone</label>
                        <input type="text" name="phone" id="phoneInput" placeholder="017xxxxxxxx" maxlength="11">
                    </div>
                    <div>
                        <label style="font-size: 12px; color: #64748b;">Designation</label>
                        <input type="text" name="designation" id="desigInput" placeholder="Designation">
                    </div>
                    <div>
                        <label style="font-size: 12px; color: #64748b;">Operator</label>
                        <select name="operator" id="operatorSelect">
                            <option value="GP">GP</option>
                            <option value="Robi">Robi</option>
                            <option value="Banglalink">Banglalink</option>
                            <option value="Airtel">Airtel</option>
                            <option value="Teletalk">Teletalk</option>
                        </select>
                    </div>
                    <div>
                        <label style="font-size: 12px; color: #64748b;">Balance (৳)</label>
                        <input type="number" name="balance" id="balanceInput" placeholder="0" value="0">
                    </div>
                    <div>
                        <button type="submit">Save Member</button>
                    </div>
                </form>
            </div>
            
            <script>
                function validateForm() {{
                    const fields = ['nameInput', 'phoneInput', 'desigInput', 'balanceInput'];
                    let hasEmpty = false;
                    
                    fields.forEach(id => {{
                        const input = document.getElementById(id);
                        if (!input.value.trim()) {{
                            input.classList.add('invalid-field');
                            hasEmpty = true;
                        }} else {{
                            input.classList.remove('invalid-field');
                        }}
                    }});

                    if (hasEmpty) {{
                        Swal.fire({{
                            icon: 'error',
                            title: 'Required Fields Empty',
                            text: 'Please fill in all the highlighted fields to save the member!',
                            confirmButtonColor: '#dc2626'
                        }});
                        return false;
                    }}

                    const phone = document.getElementById('phoneInput').value.trim();
                    const operator = document.getElementById('operatorSelect').value;
                    const phoneRegex = /^01[0-9]{{9}}$/;

                    if (!phoneRegex.test(phone)) {{
                        document.getElementById('phoneInput').classList.add('invalid-field');
                        Swal.fire({{
                            icon: 'error',
                            title: 'Invalid Phone Number',
                            text: 'Please enter a valid 11-digit Bangladeshi mobile number starting with 01.',
                            confirmButtonColor: '#3b82f6'
                        }});
                        return false;
                    }}
                    
                    const prefix = phone.substring(0, 3);
                    let valid = false;
                    let msg = '';

                    if (operator === 'GP') {{
                        if (prefix === '017' || prefix === '013') valid = true;
                        else msg = 'GP number must start with 017 or 013!';
                    }} else if (operator === 'Robi') {{
                        if (prefix === '018') valid = true;
                        else msg = 'Robi number must start with 018!';
                    }} else if (operator === 'Banglalink') {{
                        if (prefix === '019' || prefix === '014') valid = true;
                        else msg = 'Banglalink number must start with 019 or 014!';
                    }} else if (operator === 'Airtel') {{
                        if (prefix === '016') valid = true;
                        else msg = 'Airtel number must start with 016!';
                    }} else if (operator === 'Teletalk') {{
                        if (prefix === '015') valid = true;
                        else msg = 'Teletalk number must start with 015!';
                    }}

                    if (!valid) {{
                        document.getElementById('phoneInput').classList.add('invalid-field');
                        Swal.fire({{
                            icon: 'warning',
                            title: 'Operator Mismatch',
                            text: msg + ' You selected ' + operator + '.',
                            confirmButtonColor: '#3b82f6'
                        }});
                        return false;
                    }}

                    return true;
                }}
            </script>
            '''

        add_button_html = f'''<a href="/dashboard?tab=employees&show_add=1" style="background: #16a34a; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: bold; display: inline-block;">+ Add New Members</a>''' if role == "Admin" else ""

        popup_js = ""
        if show_no_data_popup:
            popup_js = f"""
            <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    Swal.fire({{
                        icon: 'warning',
                        title: 'No Data Found',
                        text: 'No member record found between {from_date} and {to_date}!',
                        confirmButtonColor: '#3b82f6'
                    }});
                }});
            </script>
            """

        edit_modal_html = """
        <div id="editBalanceModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 2000; justify-content: center; align-items: center;">
            <div style="background: white; padding: 30px; border-radius: 10px; width: 100%; max-width: 400px; box-shadow: 0 10px 25px rgba(0,0,0,0.2);">
                <h3 style="margin-top: 0; color: #1e293b;">Edit Balance for <span id="editEmpName" style="color: #3b82f6;"></span></h3>
                <form action="/update_balance" method="POST">
                    <input type="hidden" name="emp_id" id="editEmpId">
                    <div style="margin-bottom: 20px;">
                        <label style="font-size: 13px; color: #64748b; font-weight: bold;">New Balance Amount (৳)</label>
                        <input type="number" name="new_balance" id="editEmpBalance" required style="margin-top: 8px;">
                    </div>
                    <div style="display: flex; justify-content: flex-end; gap: 10px;">
                        <button type="button" onclick="closeEditModal()" style="background: #64748b;">Cancel</button>
                        <button type="submit" style="background: #16a34a;">Save Changes</button>
                    </div>
                </form>
            </div>
        </div>
        <script>
            function openEditModal(id, name, balance) {
                document.getElementById('editEmpId').value = id;
                document.getElementById('editEmpName').innerText = name;
                document.getElementById('editEmpBalance').value = balance;
                document.getElementById('editBalanceModal').style.display = 'flex';
            }
            function closeEditModal() {
                document.getElementById('editBalanceModal').style.display = 'none';
            }
        </script>
        """

        content_area = f'''
        <div class="panel">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 15px;">
                <h3 style="margin: 0;">👥 All Members List ({len(employees)})</h3>
                <div style="display: flex; gap: 15px; align-items: center; flex-wrap: wrap;">
                    <form method="GET" action="/dashboard" style="display: flex; gap: 10px; align-items: center;">
                        <input type="hidden" name="tab" value="employees">
                        <div>
                            <label style="font-size: 11px; color: #64748b; display: block;">From Date</label>
                            <input type="date" name="from_date" value="{from_date}" style="margin-top: 0; padding: 5px 8px;">
                        </div>
                        <div>
                            <label style="font-size: 11px; color: #64748b; display: block;">To Date</label>
                            <input type="date" name="to_date" value="{to_date}" style="margin-top: 0; padding: 5px 8px;">
                        </div>
                        <div style="margin-top: 15px;">
                            <button type="submit" style="padding: 6px 12px;">Filter</button>
                            <a href="/dashboard?tab=employees" style="font-size: 13px; margin-left: 5px; color: #64748b; text-decoration: none;">Reset</a>
                        </div>
                    </form>
                    <div style="margin-top: 15px;">
                        {add_button_html}
                    </div>
                </div>
            </div>
            {add_form_section}
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Phone</th>
                        <th>Designation</th>
                        <th>Operator</th>
                        <th>Balance</th>
                        <th>Date Added</th>
                        <th style="text-align: right;">Action</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        {edit_modal_html}
        ''' + popup_js
        
    elif tab == 'requisitions':
        req_rows = ""
        if len(requisitions) == 0:
            req_rows = '<tr><td colspan="6" style="text-align: center; color: #64748b;">No requisitions submitted yet.</td></tr>'
        else:
            for req in requisitions:
                if req['status'] == "Pending":
                    status_badge = '<span class="badge badge-pending">Pending</span>'
                elif req['status'] == "Approved":
                    status_badge = '<span class="badge badge-approved">Approved</span>'
                else:
                    status_badge = '<span class="badge badge-rejected">Rejected</span>'
                
                action_buttons = ""
                if role == "Admin" and req['status'] == "Pending":
                    action_buttons = f'''
                        <a href="/update_requisition/{req['id']}/Approved" style="color: #16a34a; font-weight: bold; text-decoration: none; margin-right: 10px;">Approve</a>
                        <a href="/update_requisition/{req['id']}/Rejected" style="color: #dc2626; font-weight: bold; text-decoration: none;">Reject</a>
                    '''
                else:
                    action_buttons = "<span>-</span>"
                    
                req_rows += f'''
                    <tr>
                        <td>{req['id']}</td>
                        <td><b>{req['emp_name']}</b></td>
                        <td>{req['type']}</td>
                        <td>{req['details']}</td>
                        <td>{status_badge}</td>
                        <td>{action_buttons}</td>
                    </tr>
                '''
            
        content_area = f'''
        <div class="panel">
            <h3>📋 Office Requisition List (Phone Bill & Accessories)</h3>
            <div style="background: #f8fafc; padding: 15px; border-radius: 6px; margin-bottom: 20px; border: 1px solid #e2e8f0;">
                <h4 style="margin-top: 0; color: #1e293b;">Submit New Requisition</h4>
                <form action="/add_requisition" method="POST" style="display: grid; grid-template-columns: 1fr 2fr auto; gap: 10px; align-items: end;">
                    <div>
                        <label style="font-size: 12px; color: #64748b;">Request Type</label>
                        <select name="req_type">
                            <option value="Phone Bill Increase">Phone Bill Increase</option>
                            <option value="Accessories">Accessories (Headphone/Charger)</option>
                            <option value="Others">Others</option>
                        </select>
                    </div>
                    <div>
                        <label style="font-size: 12px; color: #64748b;">Details</label>
                        <input type="text" name="details" placeholder="Describe your request..." required>
                    </div>
                    <div>
                        <button type="submit">Submit</button>
                    </div>
                </form>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Employee</th>
                        <th>Request Type</th>
                        <th>Details</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {req_rows}
                </tbody>
            </table>
        </div>
        '''
        
    elif tab == 'profile':
        role_input_html = f'''
            <select name="role">
                <option value="Admin" {"selected" if role == "Admin" else ""}>Admin</option>
                <option value="Member" {"selected" if role == "Member" else ""}>Member</option>
            </select>
        ''' if role == "Admin" else f'''
            <input type="text" value="{role}" readonly style="background: #f1f5f9; cursor: not-allowed;">
        '''

        js_code = """
        <script>
            function compressAndPreview(event) {
                const file = event.target.files[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = new Image();
                    img.onload = function() {
                        const canvas = document.createElement('canvas');
                        const ctx = canvas.getContext('2d');
                        const size = Math.min(img.width, img.height);
                        canvas.width = 100;
                        canvas.height = 100;
                        const startX = (img.width - size) / 2;
                        const startY = (img.height - size) / 2;
                        ctx.drawImage(img, startX, startY, size, size, 0, 0, 100, 100);
                        const compressedDataUrl = canvas.toDataURL('image/jpeg', 0.7);
                        document.getElementById('profileB64Input').value = compressedDataUrl;
                        document.getElementById('avatarPreviewContainer').innerHTML = '<img src="' + compressedDataUrl + '" alt="Profile" style="width:100%; height:100%; object-fit:cover;">';
                    };
                    img.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        </script>
        """

        content_area = f'''
        <div class="panel" style="max-width: 600px; margin: auto;">
            <form action="/update_profile" method="POST">
                <input type="hidden" name="profile_b64" id="profileB64Input" value="{profile_pic}">
                <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 25px;">
                    <div id="avatarPreviewContainer" onclick="document.getElementById('profileImageInput').click();" style="width: 70px; height: 70px; background: #1e293b; color: white; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 26px; font-weight: bold; overflow: hidden; cursor: pointer; border: 3px solid #3b82f6; position: relative;" title="Click to change profile picture">
                        {f'<img src="{profile_pic}" alt="Profile" style="width:100%; height:100%; object-fit:cover;">' if profile_pic else name[0].upper()}
                        <div style="position: absolute; bottom: 0; background: rgba(0,0,0,0.6); width: 100%; font-size: 9px; text-align: center; color: white; padding: 2px;">Edit</div>
                    </div>
                    <input type="file" id="profileImageInput" accept="image/*" style="display: none;" onchange="compressAndPreview(event)">
                    <div>
                        <h3 style="margin: 0; color: #1e293b;">Profile Customization</h3>
                        <p style="margin: 2px 0 0 0; color: #64748b; font-size: 13px;">Click on the avatar icon to choose a picture from your gallery.</p>
                    </div>
                </div>
                <div style="margin-bottom: 15px;">
                    <label style="font-size: 13px; color: #64748b; font-weight: bold;">Full Name</label>
                    <input type="text" name="name" value="{name}" required>
                </div>
                <div style="margin-bottom: 15px;">
                    <label style="font-size: 13px; color: #64748b; font-weight: bold;">User ID</label>
                    <input type="text" name="user_id" value="{user_id}" required>
                </div>
                <div style="margin-bottom: 15px;">
                    <label style="font-size: 13px; color: #64748b; font-weight: bold;">Role</label>
                    {role_input_html}
                </div>
                <button type="submit">Save Changes</button>
            </form>
        </div>
        ''' + js_code

    elif tab == 'activity_log':
        log_rows = ""
        for log in logs:
            log_rows += f'<tr><td>{log["timestamp"]}</td><td>{log["action"]}</td></tr>'
            
        content_area = f'''
        <div class="panel">
            <h3>📜 System Activity Log</h3>
            <p style="color: #64748b; margin-bottom: 15px;">Recent system actions and user activities.</p>
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Activity Description</th>
                    </tr>
                </thead>
                <tbody>
                    {log_rows if log_rows else '<tr><td colspan="2">No logs found.</td></tr>'}
                </tbody>
            </table>
        </div>
        '''

    elif tab == 'settings':
        content_area = '''
        <div class="panel" style="max-width: 600px; margin: auto;">
            <h3>⚙️ Settings</h3>
            <p style="color: #64748b; margin-bottom: 20px;">System preferences and account configurations.</p>
            <div style="margin-bottom: 15px;">
                <label style="font-size: 13px; color: #64748b; font-weight: bold;">System Theme</label>
                <select style="margin-top: 5px;">
                    <option value="light">Light Mode (Default)</option>
                    <option value="dark">Dark Mode</option>
                </select>
            </div>
            <div style="margin-bottom: 15px;">
                <label style="font-size: 13px; color: #64748b; font-weight: bold;">Notifications</label>
                <select style="margin-top: 5px;">
                    <option value="enabled">Enabled</option>
                    <option value="disabled">Disabled</option>
                </select>
            </div>
            <button type="button" onclick="alert('Settings updated successfully!')">Save Preferences</button>
        </div>
        '''

    body_content = f'''
    <div class="top-header">
        {brand_header_html}
        <div class="user-profile-area" onclick="toggleProfileMenu()">
            <div class="user-meta">
                <div class="user-name-display">
                    <span class="badge {'badge-admin' if role == 'Admin' else 'badge-member'}">{role}</span>
                    {name}
                </div>
                <div class="user-id-display">ID: {user_id}</div>
            </div>
            <div class="user-avatar">
                {avatar_html}
            </div>
            <div class="profile-dropdown" id="profileDropdown">
                <div class="dropdown-header-info">
                    <div class="d-name">{name}</div>
                    <div class="d-email">{user_email}</div>
                </div>
                <a href="/dashboard?tab=profile">👤 Profile</a>
                <a href="/dashboard?tab=activity_log">🕒 Activity Log</a>
                <a href="/dashboard?tab=settings">⚙️ Settings</a>
                <a href="/logout" class="logout-btn">🔴 Logout</a>
            </div>
        </div>
    </div>
    <div class="app-layout">
        <div class="sidebar">
            <a href="/dashboard?tab=overview" class="{'active' if tab == 'overview' else ''}">📊 Dashboard</a>
            <a href="/dashboard?tab=employees" class="{'active' if tab == 'employees' else ''}">👥 All Members List</a>
            <a href="/dashboard?tab=requisitions" class="{'active' if tab == 'requisitions' else ''}">📋 Office Requisition</a>
            <a href="/dashboard?tab=settings" class="{'active' if tab == 'settings' else ''}">⚙️ Settings</a>
        </div>
        <div class="main-content">
            {('<div class="success">' + msg + '</div>') if msg else ''}
            {content_area}
        </div>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE, title="Dashboard - Fu Info Tech", content=body_content)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    new_name = request.form.get('name')
    new_user_id = request.form.get('user_id')
    profile_b64 = request.form.get('profile_b64')
    if new_name: session['name'] = new_name
    if new_user_id: session['user_id'] = new_user_id
    if profile_b64: session['profile_pic'] = profile_b64
    if session.get('role') == 'Admin':
        new_role = request.form.get('role')
        if new_role: session['role'] = new_role
    conn = sqlite3.connect('fu_infotech.db')
    conn.execute("INSERT INTO activity_logs (action, timestamp) VALUES (?, ?)", 
                 ("Updated profile settings", get_bd_time_string()))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard', tab='profile', msg="Profile updated successfully!"))

@app.route('/add_employee', methods=['POST'])
def add_employee():
    if not session.get('logged_in') or session.get('role') != 'Admin':
        return redirect(url_for('login'))
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    designation = request.form.get('designation', '').strip()
    operator = request.form.get('operator')
    balance = int(request.form.get('balance', 0))
    
    if not name or not phone or not designation:
        return redirect(url_for('dashboard', tab='employees', msg="Error: All fields are required!"))

    if not phone.isdigit() or len(phone) != 11 or not phone.startswith('01'):
        return redirect(url_for('dashboard', tab='employees', msg="Error: Invalid phone number format!"))
    
    prefix = phone[:3]
    valid = False
    if operator == 'GP' and prefix in ['017', '013']: valid = True
    elif operator == 'Robi' and prefix == '018': valid = True
    elif operator == 'Banglalink' and prefix in ['019', '014']: valid = True
    elif operator == 'Airtel' and prefix == '016': valid = True
    elif operator == 'Teletalk' and prefix == '015': valid = True
    
    if not valid:
        return redirect(url_for('dashboard', tab='employees', msg=f"Error: Phone prefix {prefix} does not match selected operator {operator}!"))
    
    current_bd_date = datetime.now(BD_TIMEZONE).strftime('%Y-%m-%d')
    conn = sqlite3.connect('fu_infotech.db')
    conn.execute("INSERT INTO employees (name, phone, designation, operator, balance, used, created_date) VALUES (?, ?, ?, ?, ?, 0, ?)",
                 (name, phone, designation, operator, balance, current_bd_date))
    conn.execute("INSERT INTO activity_logs (action, timestamp) VALUES (?, ?)", 
                 (f"Admin added new member: {name} ({phone})", get_bd_time_string()))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard', tab='employees', msg=f"Member {name} added successfully!"))

@app.route('/delete_member/<int:emp_id>')
def delete_member(emp_id):
    if not session.get('logged_in') or session.get('role') != 'Admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('fu_infotech.db')
    conn.row_factory = sqlite3.Row
    emp = conn.execute("SELECT * FROM employees WHERE id = ?", (emp_id,)).fetchone()
    
    if emp:
        conn.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
        conn.execute("INSERT INTO activity_logs (action, timestamp) VALUES (?, ?)", 
                     (f"Admin deleted member: {emp['name']}", get_bd_time_string()))
        conn.commit()
        msg = f"Member {emp['name']} deleted successfully!"
    else:
        msg = "Member not found!"
        
    conn.close()
    return redirect(url_for('dashboard', tab='employees', msg=msg))

@app.route('/update_balance', methods=['POST'])
def update_balance():
    if not session.get('logged_in') or session.get('role') != 'Admin':
        return redirect(url_for('login'))
    emp_id = request.form.get('emp_id')
    new_balance = int(request.form.get('new_balance', 0))
    conn = sqlite3.connect('fu_infotech.db')
    conn.row_factory = sqlite3.Row
    emp = conn.execute("SELECT * FROM employees WHERE id = ?", (emp_id,)).fetchone()
    if emp:
        conn.execute("UPDATE employees SET balance = ? WHERE id = ?", (new_balance, emp_id))
        conn.execute("INSERT INTO activity_logs (action, timestamp) VALUES (?, ?)", 
                     (f"Updated balance for {emp['name']} to ৳{new_balance}", get_bd_time_string()))
        conn.commit()
    conn.close()
    return redirect(url_for('dashboard', tab='employees', msg=f"Balance updated successfully for {emp['name'] if emp else 'Member'}!"))

@app.route('/print_member/<int:emp_id>')
def print_member(emp_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = sqlite3.connect('fu_infotech.db')
    conn.row_factory = sqlite3.Row
    emp = conn.execute("SELECT * FROM employees WHERE id = ?", (emp_id,)).fetchone()
    conn.close()
    if not emp:
        return "Member not found", 404
        
    print_template = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Print Report - {emp['name']}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; color: #333; }}
            .print-container {{ max-width: 700px; margin: auto; border: 2px solid #1e293b; padding: 35px; border-radius: 8px; background: #fff; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #3b82f6; padding-bottom: 20px; margin-bottom: 25px; }}
            .logo-area {{ display: flex; align-items: center; gap: 12px; }}
            .logo-area img {{ height: 45px; }}
            .company-title {{ font-size: 22px; font-weight: bold; color: #1e293b; }}
            .company-title span {{ color: #3b82f6; }}
            .report-title {{ text-align: center; font-size: 18px; font-weight: bold; color: #475569; margin-bottom: 25px; text-transform: uppercase; letter-spacing: 1px; }}
            .info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
            .info-table th, .info-table td {{ border: 1px solid #cbd5e1; padding: 12px 15px; font-size: 15px; text-align: left; }}
            .info-table th {{ background-color: #f8fafc; color: #1e293b; width: 35%; }}
            .footer {{ display: flex; justify-content: space-between; margin-top: 50px; padding-top: 20px; border-top: 1px solid #cbd5e1; font-size: 14px; color: #64748b; }}
            .signature-box {{ text-align: center; margin-top: 60px; }}
            .signature-line {{ border-top: 1px solid #333; width: 200px; margin: auto; margin-bottom: 5px; }}
            @media print {{
                body {{ margin: 0; background: #fff; }}
                .print-container {{ border: none; padding: 0; }}
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body onload="window.print()">
        <div class="print-container">
            <div class="header">
                <div class="logo-area">
                    <img src="https://i.ibb.co/3s65q52/download.png" alt="FU INFOTECH">
                    <div class="company-title">FU <span>INFOTECH</span></div>
                </div>
                <div style="text-align: right; font-size: 13px; color: #64748b;">
                    <div>Official Member Report</div>
                    <div>Date: {emp['created_date'] if 'created_date' in emp.keys() and emp['created_date'] else datetime.now(BD_TIMEZONE).strftime('%Y-%m-%d')}</div>
                </div>
            </div>
            <div class="report-title">Member Financial Summary & Details</div>
            <table class="info-table">
                <tr>
                    <th>Member Name</th>
                    <td><b>{emp['name']}</b></td>
                </tr>
                <tr>
                    <th>Mobile Number</th>
                    <td>{emp['phone']}</td>
                </tr>
                <tr>
                    <th>Designation</th>
                    <td>{emp['designation']}</td>
                </tr>
                <tr>
                    <th>Operator</th>
                    <td>{emp['operator']}</td>
                </tr>
                <tr>
                    <th>Current Balance</th>
                    <td style="color: #16a34a; font-weight: bold; font-size: 16px;">৳{emp['balance']}</td>
                </tr>
                <tr>
                    <th>Registration Date</th>
                    <td>{emp['created_date'] if 'created_date' in emp.keys() and emp['created_date'] else datetime.now(BD_TIMEZONE).strftime('%Y-%m-%d')}</td>
                </tr>
            </table>
            <div style="display: flex; justify-content: space-between; margin-top: 80px;">
                <div class="signature-box">
                    <div class="signature-line"></div>
                    <div style="font-size: 13px; font-weight: bold;">Prepared By</div>
                </div>
                <div class="signature-box">
                    <div class="signature-line"></div>
                    <div style="font-size: 13px; font-weight: bold;">Authorized Signature</div>
                </div>
            </div>
            <div class="footer">
                <div>FU INFOTECH Management System</div>
                <div>System Generated Report</div>
            </div>
        </div>
        <div style="text-align: center; margin-top: 25px;" class="no-print">
            <button onclick="window.print()" style="background: #3b82f6; padding: 10px 20px; font-size: 14px; border-radius: 6px; color: white; border: none; cursor: pointer;">Print Again</button>
            <button onclick="window.close()" style="background: #64748b; padding: 10px 20px; font-size: 14px; border-radius: 6px; color: white; border: none; cursor: pointer; margin-left: 10px;">Close</button>
        </div>
    </body>
    </html>
    '''
    return render_template_string(print_template)

@app.route('/add_requisition', methods=['POST'])
def add_requisition():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    user = session.get('user_id', session.get('user'))
    req_type = request.form.get('req_type')
    details = request.form.get('details')
    conn = sqlite3.connect('fu_infotech.db')
    conn.execute("INSERT INTO requisitions (emp_name, type, details, status) VALUES (?, ?, ?, 'Pending')",
                 (user, req_type, details))
    conn.execute("INSERT INTO activity_logs (action, timestamp) VALUES (?, ?)", 
                 (f"User submitted a requisition for {req_type}", get_bd_time_string()))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard', tab='requisitions', msg="Requisition submitted successfully!"))

@app.route('/update_requisition/<int:req_id>/<status>')
def update_requisition(req_id, status):
    if not session.get('logged_in') or session.get('role') != 'Admin':
        return redirect(url_for('login'))
    conn = sqlite3.connect('fu_infotech.db')
    conn.execute("UPDATE requisitions SET status = ? WHERE id = ?", (status, req_id))
    conn.execute("INSERT INTO activity_logs (action, timestamp) VALUES (?, ?)", 
                 (f"Admin marked requisition #{req_id} as {status}", get_bd_time_string()))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard', tab='requisitions', msg=f"Requisition has been {status.lower()}!"))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)