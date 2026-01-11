import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, g

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.secret_key = os.environ.get('SECRET_KEY', 'college-tracker-2024')

# Use /tmp for database on Vercel (serverless), otherwise use local
if os.environ.get('VERCEL'):
    DATABASE = '/tmp/tracker.db'
else:
    DATABASE = os.path.join(BASE_DIR, 'tracker.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY,
                gpa REAL,
                sat_score INTEGER,
                act_score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS colleges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT,
                type TEXT DEFAULT 'reach',
                deadline_type TEXT DEFAULT 'rd',
                deadline_date DATE,
                status TEXT DEFAULT 'researching',
                result TEXT,
                avg_gpa REAL,
                acceptance_rate REAL,
                portal_url TEXT,
                notes TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                college_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                is_done INTEGER DEFAULT 0,
                due_date DATE,
                FOREIGN KEY (college_id) REFERENCES colleges (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS essays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                college_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                prompt TEXT,
                word_limit INTEGER,
                status TEXT DEFAULT 'not_started',
                FOREIGN KEY (college_id) REFERENCES colleges (id) ON DELETE CASCADE
            );

            INSERT OR IGNORE INTO profile (id, gpa, sat_score, act_score) VALUES (1, NULL, NULL, NULL);
        ''')
        db.commit()

init_db()

STATUSES = [
    ('researching', 'Researching', '#64748b', 'bg-slate-100'),
    ('preparing', 'Preparing', '#f59e0b', 'bg-amber-100'),
    ('in_progress', 'In Progress', '#3b82f6', 'bg-blue-100'),
    ('submitted', 'Submitted', '#8b5cf6', 'bg-violet-100'),
    ('interview', 'Interview', '#ec4899', 'bg-pink-100'),
    ('accepted', 'Accepted', '#10b981', 'bg-emerald-100'),
    ('waitlisted', 'Waitlisted', '#f97316', 'bg-orange-100'),
    ('rejected', 'Rejected', '#ef4444', 'bg-red-100'),
    ('withdrawn', 'Withdrawn', '#6b7280', 'bg-gray-100'),
]

DEADLINE_TYPES = [
    ('ed', 'Early Decision', 'Nov 1-15'),
    ('ed2', 'Early Decision II', 'Jan 1-15'),
    ('ea', 'Early Action', 'Nov 1-15'),
    ('rea', 'Restrictive EA', 'Nov 1'),
    ('rd', 'Regular Decision', 'Jan 1-15'),
    ('rolling', 'Rolling', 'Varies'),
]

SCHOOL_TYPES = [
    ('safety', 'Safety', '#10b981'),
    ('match', 'Match', '#3b82f6'),
    ('reach', 'Reach', '#f59e0b'),
    ('far_reach', 'Far Reach', '#ef4444'),
]

# College database for autocomplete (name, location, avg_gpa, acceptance_rate, rd_date, ea_date, ed_date, portal_url)
COLLEGE_DATABASE = [
    {"name": "Harvard University", "location": "Cambridge, MA", "avg_gpa": 3.9, "acceptance_rate": 3.2, "rd": "2026-01-01", "rea": "2025-11-01", "portal": "https://college.harvard.edu/admissions"},
    {"name": "Stanford University", "location": "Stanford, CA", "avg_gpa": 3.96, "acceptance_rate": 3.7, "rd": "2026-01-02", "rea": "2025-11-01", "portal": "https://admission.stanford.edu"},
    {"name": "MIT", "location": "Cambridge, MA", "avg_gpa": 3.95, "acceptance_rate": 3.9, "rd": "2026-01-04", "ea": "2025-11-01", "portal": "https://mitadmissions.org"},
    {"name": "Yale University", "location": "New Haven, CT", "avg_gpa": 3.95, "acceptance_rate": 4.5, "rd": "2026-01-02", "rea": "2025-11-01", "portal": "https://admissions.yale.edu"},
    {"name": "Princeton University", "location": "Princeton, NJ", "avg_gpa": 3.91, "acceptance_rate": 4.0, "rd": "2026-01-01", "rea": "2025-11-01", "portal": "https://admission.princeton.edu"},
    {"name": "Columbia University", "location": "New York, NY", "avg_gpa": 3.91, "acceptance_rate": 3.9, "rd": "2026-01-01", "ed": "2025-11-01", "portal": "https://undergrad.admissions.columbia.edu"},
    {"name": "University of Chicago", "location": "Chicago, IL", "avg_gpa": 3.92, "acceptance_rate": 5.4, "rd": "2026-01-04", "ea": "2025-11-01", "ed": "2025-11-01", "portal": "https://collegeadmissions.uchicago.edu"},
    {"name": "Duke University", "location": "Durham, NC", "avg_gpa": 3.94, "acceptance_rate": 6.0, "rd": "2026-01-03", "ed": "2025-11-01", "portal": "https://admissions.duke.edu"},
    {"name": "Northwestern University", "location": "Evanston, IL", "avg_gpa": 3.92, "acceptance_rate": 7.0, "rd": "2026-01-03", "ed": "2025-11-01", "portal": "https://admissions.northwestern.edu"},
    {"name": "Brown University", "location": "Providence, RI", "avg_gpa": 3.94, "acceptance_rate": 5.1, "rd": "2026-01-03", "ed": "2025-11-01", "portal": "https://admission.brown.edu"},
    {"name": "Dartmouth College", "location": "Hanover, NH", "avg_gpa": 3.9, "acceptance_rate": 6.2, "rd": "2026-01-03", "ed": "2025-11-01", "portal": "https://admissions.dartmouth.edu"},
    {"name": "Cornell University", "location": "Ithaca, NY", "avg_gpa": 3.9, "acceptance_rate": 7.3, "rd": "2026-01-02", "ed": "2025-11-01", "portal": "https://admissions.cornell.edu"},
    {"name": "University of Pennsylvania", "location": "Philadelphia, PA", "avg_gpa": 3.9, "acceptance_rate": 5.9, "rd": "2026-01-05", "ed": "2025-11-01", "portal": "https://admissions.upenn.edu"},
    {"name": "Vanderbilt University", "location": "Nashville, TN", "avg_gpa": 3.88, "acceptance_rate": 6.7, "rd": "2026-01-01", "ed": "2025-11-01", "portal": "https://admissions.vanderbilt.edu"},
    {"name": "Rice University", "location": "Houston, TX", "avg_gpa": 3.96, "acceptance_rate": 8.7, "rd": "2026-01-04", "ed": "2025-11-01", "portal": "https://admission.rice.edu"},
    {"name": "Washington University in St. Louis", "location": "St. Louis, MO", "avg_gpa": 3.93, "acceptance_rate": 11.0, "rd": "2026-01-04", "ed": "2025-11-01", "portal": "https://admissions.wustl.edu"},
    {"name": "University of Notre Dame", "location": "Notre Dame, IN", "avg_gpa": 3.9, "acceptance_rate": 12.9, "rd": "2026-01-01", "rea": "2025-11-01", "portal": "https://admissions.nd.edu"},
    {"name": "Georgetown University", "location": "Washington, DC", "avg_gpa": 3.9, "acceptance_rate": 12.0, "rd": "2026-01-10", "ea": "2025-11-01", "portal": "https://uadmissions.georgetown.edu"},
    {"name": "Carnegie Mellon University", "location": "Pittsburgh, PA", "avg_gpa": 3.89, "acceptance_rate": 11.0, "rd": "2026-01-03", "ed": "2025-11-01", "portal": "https://admission.enrollment.cmu.edu"},
    {"name": "Emory University", "location": "Atlanta, GA", "avg_gpa": 3.86, "acceptance_rate": 11.4, "rd": "2026-01-01", "ed": "2025-11-01", "portal": "https://apply.emory.edu"},
    {"name": "University of Virginia", "location": "Charlottesville, VA", "avg_gpa": 3.88, "acceptance_rate": 18.7, "rd": "2026-01-05", "ea": "2025-11-01", "portal": "https://admission.virginia.edu"},
    {"name": "University of Michigan", "location": "Ann Arbor, MI", "avg_gpa": 3.9, "acceptance_rate": 17.7, "rd": "2026-02-01", "ea": "2025-11-01", "portal": "https://admissions.umich.edu"},
    {"name": "USC (University of Southern California)", "location": "Los Angeles, CA", "avg_gpa": 3.85, "acceptance_rate": 12.0, "rd": "2026-01-15", "portal": "https://admission.usc.edu"},
    {"name": "UCLA", "location": "Los Angeles, CA", "avg_gpa": 3.93, "acceptance_rate": 8.8, "rd": "2025-11-30", "portal": "https://admission.ucla.edu"},
    {"name": "UC Berkeley", "location": "Berkeley, CA", "avg_gpa": 3.91, "acceptance_rate": 11.6, "rd": "2025-11-30", "portal": "https://admissions.berkeley.edu"},
    {"name": "UC San Diego", "location": "La Jolla, CA", "avg_gpa": 3.85, "acceptance_rate": 24.7, "rd": "2025-11-30", "portal": "https://admissions.ucsd.edu"},
    {"name": "UC Santa Barbara", "location": "Santa Barbara, CA", "avg_gpa": 3.8, "acceptance_rate": 25.9, "rd": "2025-11-30", "portal": "https://admissions.ucsb.edu"},
    {"name": "UC Irvine", "location": "Irvine, CA", "avg_gpa": 3.82, "acceptance_rate": 21.0, "rd": "2025-11-30", "portal": "https://admissions.uci.edu"},
    {"name": "UC Davis", "location": "Davis, CA", "avg_gpa": 3.78, "acceptance_rate": 37.3, "rd": "2025-11-30", "portal": "https://admissions.ucdavis.edu"},
    {"name": "Boston University", "location": "Boston, MA", "avg_gpa": 3.71, "acceptance_rate": 14.0, "rd": "2026-01-04", "ed": "2025-11-01", "portal": "https://bu.edu/admissions"},
    {"name": "Boston College", "location": "Chestnut Hill, MA", "avg_gpa": 3.85, "acceptance_rate": 17.0, "rd": "2026-01-01", "ea": "2025-11-01", "portal": "https://bc.edu/admission"},
    {"name": "New York University", "location": "New York, NY", "avg_gpa": 3.7, "acceptance_rate": 12.2, "rd": "2026-01-05", "ed": "2025-11-01", "portal": "https://admissions.nyu.edu"},
    {"name": "Tufts University", "location": "Medford, MA", "avg_gpa": 3.85, "acceptance_rate": 10.0, "rd": "2026-01-03", "ed": "2025-11-01", "portal": "https://admissions.tufts.edu"},
    {"name": "University of Florida", "location": "Gainesville, FL", "avg_gpa": 3.8, "acceptance_rate": 23.0, "rd": "2025-11-01", "portal": "https://admissions.ufl.edu"},
    {"name": "Georgia Tech", "location": "Atlanta, GA", "avg_gpa": 3.85, "acceptance_rate": 16.0, "rd": "2026-01-04", "ea": "2025-11-01", "portal": "https://admission.gatech.edu"},
    {"name": "University of North Carolina at Chapel Hill", "location": "Chapel Hill, NC", "avg_gpa": 3.85, "acceptance_rate": 17.0, "rd": "2026-01-15", "ea": "2025-10-15", "portal": "https://admissions.unc.edu"},
    {"name": "University of Texas at Austin", "location": "Austin, TX", "avg_gpa": 3.75, "acceptance_rate": 29.0, "rd": "2025-12-01", "portal": "https://admissions.utexas.edu"},
    {"name": "University of Wisconsin-Madison", "location": "Madison, WI", "avg_gpa": 3.8, "acceptance_rate": 49.0, "rd": "2026-02-01", "ea": "2025-11-01", "portal": "https://admissions.wisc.edu"},
    {"name": "Penn State University", "location": "University Park, PA", "avg_gpa": 3.6, "acceptance_rate": 55.0, "rd": "2025-11-30", "portal": "https://admissions.psu.edu", "rolling": True},
    {"name": "Ohio State University", "location": "Columbus, OH", "avg_gpa": 3.7, "acceptance_rate": 53.0, "rd": "2026-02-01", "ea": "2025-11-01", "portal": "https://undergrad.osu.edu"},
    {"name": "Purdue University", "location": "West Lafayette, IN", "avg_gpa": 3.7, "acceptance_rate": 53.0, "rd": "2026-01-15", "ea": "2025-11-01", "portal": "https://admissions.purdue.edu"},
    {"name": "Indiana University Bloomington", "location": "Bloomington, IN", "avg_gpa": 3.6, "acceptance_rate": 80.0, "rd": "2026-02-01", "portal": "https://admissions.indiana.edu", "rolling": True},
    {"name": "University of Illinois Urbana-Champaign", "location": "Champaign, IL", "avg_gpa": 3.75, "acceptance_rate": 45.0, "rd": "2026-01-05", "ea": "2025-11-01", "portal": "https://admissions.illinois.edu"},
    {"name": "University of Washington", "location": "Seattle, WA", "avg_gpa": 3.8, "acceptance_rate": 48.0, "rd": "2025-11-15", "portal": "https://admit.washington.edu"},
    {"name": "University of Maryland", "location": "College Park, MD", "avg_gpa": 3.8, "acceptance_rate": 45.0, "rd": "2026-01-20", "ea": "2025-11-01", "portal": "https://admissions.umd.edu"},
    {"name": "Virginia Tech", "location": "Blacksburg, VA", "avg_gpa": 3.7, "acceptance_rate": 57.0, "rd": "2026-01-15", "ed": "2025-11-01", "portal": "https://admissions.vt.edu"},
    {"name": "Clemson University", "location": "Clemson, SC", "avg_gpa": 3.7, "acceptance_rate": 43.0, "rd": "2026-05-01", "portal": "https://clemson.edu/admissions", "rolling": True},
    {"name": "University of Pittsburgh", "location": "Pittsburgh, PA", "avg_gpa": 3.7, "acceptance_rate": 42.0, "rd": "2025-12-01", "portal": "https://admissions.pitt.edu", "rolling": True},
    {"name": "Northeastern University", "location": "Boston, MA", "avg_gpa": 3.8, "acceptance_rate": 6.7, "rd": "2026-01-01", "ed": "2025-11-01", "portal": "https://admissions.northeastern.edu"},
    {"name": "Case Western Reserve University", "location": "Cleveland, OH", "avg_gpa": 3.8, "acceptance_rate": 27.0, "rd": "2026-01-15", "ea": "2025-11-01", "portal": "https://admission.case.edu"},
    {"name": "Tulane University", "location": "New Orleans, LA", "avg_gpa": 3.6, "acceptance_rate": 11.0, "rd": "2026-01-15", "ea": "2025-11-15", "portal": "https://admission.tulane.edu"},
    {"name": "University of Rochester", "location": "Rochester, NY", "avg_gpa": 3.75, "acceptance_rate": 39.0, "rd": "2026-01-05", "ed": "2025-11-01", "portal": "https://enrollment.rochester.edu"},
    {"name": "Wake Forest University", "location": "Winston-Salem, NC", "avg_gpa": 3.81, "acceptance_rate": 21.0, "rd": "2026-01-01", "ed": "2025-11-15", "portal": "https://admissions.wfu.edu"},
    {"name": "Brandeis University", "location": "Waltham, MA", "avg_gpa": 3.8, "acceptance_rate": 33.0, "rd": "2026-01-01", "ed": "2025-11-01", "portal": "https://brandeis.edu/admissions"},
    {"name": "William & Mary", "location": "Williamsburg, VA", "avg_gpa": 3.9, "acceptance_rate": 33.0, "rd": "2026-01-01", "ed": "2025-11-01", "portal": "https://admission.wm.edu"},
    {"name": "Lehigh University", "location": "Bethlehem, PA", "avg_gpa": 3.7, "acceptance_rate": 32.0, "rd": "2026-01-01", "ed": "2025-11-01", "portal": "https://admissions.lehigh.edu"},
    {"name": "Colgate University", "location": "Hamilton, NY", "avg_gpa": 3.8, "acceptance_rate": 13.0, "rd": "2026-01-15", "ed": "2025-11-15", "portal": "https://colgate.edu/admission"},
    {"name": "Williams College", "location": "Williamstown, MA", "avg_gpa": 3.95, "acceptance_rate": 9.0, "rd": "2026-01-08", "ed": "2025-11-15", "portal": "https://admission.williams.edu"},
    {"name": "Amherst College", "location": "Amherst, MA", "avg_gpa": 3.92, "acceptance_rate": 7.0, "rd": "2026-01-03", "ed": "2025-11-01", "portal": "https://amherst.edu/admission"},
    {"name": "Swarthmore College", "location": "Swarthmore, PA", "avg_gpa": 3.9, "acceptance_rate": 7.0, "rd": "2026-01-04", "ed": "2025-11-15", "portal": "https://swarthmore.edu/admissions"},
    {"name": "Pomona College", "location": "Claremont, CA", "avg_gpa": 3.93, "acceptance_rate": 7.0, "rd": "2026-01-08", "ed": "2025-11-15", "portal": "https://pomona.edu/admissions"},
    {"name": "Bowdoin College", "location": "Brunswick, ME", "avg_gpa": 3.89, "acceptance_rate": 9.0, "rd": "2026-01-05", "ed": "2025-11-15", "portal": "https://bowdoin.edu/admissions"},
    {"name": "Middlebury College", "location": "Middlebury, VT", "avg_gpa": 3.87, "acceptance_rate": 13.0, "rd": "2026-01-01", "ed": "2025-11-15", "portal": "https://middlebury.edu/admissions"},
    {"name": "Wellesley College", "location": "Wellesley, MA", "avg_gpa": 3.9, "acceptance_rate": 13.0, "rd": "2026-01-08", "ed": "2025-11-01", "portal": "https://wellesley.edu/admission"},
    {"name": "Barnard College", "location": "New York, NY", "avg_gpa": 3.9, "acceptance_rate": 9.0, "rd": "2026-01-04", "ed": "2025-11-01", "portal": "https://barnard.edu/admissions"},
    {"name": "Harvey Mudd College", "location": "Claremont, CA", "avg_gpa": 3.95, "acceptance_rate": 13.0, "rd": "2026-01-05", "ed": "2025-11-15", "portal": "https://hmc.edu/admission"},
    {"name": "Claremont McKenna College", "location": "Claremont, CA", "avg_gpa": 3.85, "acceptance_rate": 11.0, "rd": "2026-01-10", "ed": "2025-11-01", "portal": "https://cmc.edu/admission"},
    {"name": "Davidson College", "location": "Davidson, NC", "avg_gpa": 3.88, "acceptance_rate": 17.0, "rd": "2026-01-05", "ed": "2025-11-15", "portal": "https://davidson.edu/admission"},
    {"name": "Grinnell College", "location": "Grinnell, IA", "avg_gpa": 3.85, "acceptance_rate": 10.0, "rd": "2026-01-15", "ed": "2025-11-15", "portal": "https://grinnell.edu/admission"},
    {"name": "Hamilton College", "location": "Clinton, NY", "avg_gpa": 3.85, "acceptance_rate": 12.0, "rd": "2026-01-08", "ed": "2025-11-15", "portal": "https://hamilton.edu/admission"},
    {"name": "Haverford College", "location": "Haverford, PA", "avg_gpa": 3.9, "acceptance_rate": 14.0, "rd": "2026-01-15", "ed": "2025-11-15", "portal": "https://haverford.edu/admission"},
    {"name": "Vassar College", "location": "Poughkeepsie, NY", "avg_gpa": 3.85, "acceptance_rate": 19.0, "rd": "2026-01-01", "ed": "2025-11-15", "portal": "https://vassar.edu/admissions"},
    {"name": "Wesleyan University", "location": "Middletown, CT", "avg_gpa": 3.87, "acceptance_rate": 14.0, "rd": "2026-01-01", "ed": "2025-11-15", "portal": "https://wesleyan.edu/admission"},
    {"name": "Carleton College", "location": "Northfield, MN", "avg_gpa": 3.9, "acceptance_rate": 16.0, "rd": "2026-01-15", "ed": "2025-11-15", "portal": "https://carleton.edu/admissions"},
    {"name": "Oberlin College", "location": "Oberlin, OH", "avg_gpa": 3.8, "acceptance_rate": 36.0, "rd": "2026-01-15", "ed": "2025-11-15", "portal": "https://oberlin.edu/admissions"},
    {"name": "Colorado College", "location": "Colorado Springs, CO", "avg_gpa": 3.8, "acceptance_rate": 11.0, "rd": "2026-01-15", "ed": "2025-11-15", "portal": "https://coloradocollege.edu/admission"},
    {"name": "Bates College", "location": "Lewiston, ME", "avg_gpa": 3.7, "acceptance_rate": 14.0, "rd": "2026-01-01", "ed": "2025-11-15", "portal": "https://bates.edu/admission"},
    {"name": "Colby College", "location": "Waterville, ME", "avg_gpa": 3.8, "acceptance_rate": 10.0, "rd": "2026-01-01", "ed": "2025-11-15", "portal": "https://colby.edu/admission"},
    {"name": "Bucknell University", "location": "Lewisburg, PA", "avg_gpa": 3.6, "acceptance_rate": 35.0, "rd": "2026-01-15", "ed": "2025-11-15", "portal": "https://bucknell.edu/admissions"},
    {"name": "University of Richmond", "location": "Richmond, VA", "avg_gpa": 3.75, "acceptance_rate": 24.0, "rd": "2026-01-01", "ed": "2025-11-01", "portal": "https://richmond.edu/admission"},
    {"name": "Macalester College", "location": "St. Paul, MN", "avg_gpa": 3.8, "acceptance_rate": 28.0, "rd": "2026-01-15", "ed": "2025-11-15", "portal": "https://macalester.edu/admissions"},
    {"name": "Scripps College", "location": "Claremont, CA", "avg_gpa": 3.85, "acceptance_rate": 29.0, "rd": "2026-01-05", "ed": "2025-11-01", "portal": "https://scrippscollege.edu/admission"},
    {"name": "Kenyon College", "location": "Gambier, OH", "avg_gpa": 3.8, "acceptance_rate": 30.0, "rd": "2026-01-15", "ed": "2025-11-15", "portal": "https://kenyon.edu/admissions"},
    {"name": "University of Miami", "location": "Coral Gables, FL", "avg_gpa": 3.7, "acceptance_rate": 28.0, "rd": "2026-01-15", "ea": "2025-11-01", "portal": "https://admissions.miami.edu"},
    {"name": "Pepperdine University", "location": "Malibu, CA", "avg_gpa": 3.7, "acceptance_rate": 32.0, "rd": "2026-01-15", "ea": "2025-11-01", "portal": "https://seaver.pepperdine.edu/admission"},
    {"name": "Santa Clara University", "location": "Santa Clara, CA", "avg_gpa": 3.75, "acceptance_rate": 49.0, "rd": "2026-01-07", "ea": "2025-11-01", "portal": "https://scu.edu/admission"},
    {"name": "Loyola Marymount University", "location": "Los Angeles, CA", "avg_gpa": 3.7, "acceptance_rate": 43.0, "rd": "2026-01-15", "ea": "2025-11-01", "portal": "https://admission.lmu.edu"},
    {"name": "Fordham University", "location": "New York, NY", "avg_gpa": 3.6, "acceptance_rate": 46.0, "rd": "2026-01-01", "ea": "2025-11-01", "portal": "https://fordham.edu/admissions"},
    {"name": "Syracuse University", "location": "Syracuse, NY", "avg_gpa": 3.6, "acceptance_rate": 45.0, "rd": "2026-01-05", "ed": "2025-11-15", "portal": "https://admissions.syr.edu"},
    {"name": "Rensselaer Polytechnic Institute", "location": "Troy, NY", "avg_gpa": 3.8, "acceptance_rate": 57.0, "rd": "2026-01-15", "ed": "2025-11-01", "portal": "https://admissions.rpi.edu"},
    {"name": "Worcester Polytechnic Institute", "location": "Worcester, MA", "avg_gpa": 3.8, "acceptance_rate": 52.0, "rd": "2026-02-01", "ea": "2025-11-01", "portal": "https://wpi.edu/admissions"},
    {"name": "Stevens Institute of Technology", "location": "Hoboken, NJ", "avg_gpa": 3.8, "acceptance_rate": 41.0, "rd": "2026-02-01", "ed": "2025-11-15", "portal": "https://stevens.edu/admissions"},
    {"name": "Rochester Institute of Technology", "location": "Rochester, NY", "avg_gpa": 3.7, "acceptance_rate": 66.0, "rd": "2026-01-15", "ed": "2025-11-01", "portal": "https://rit.edu/admissions"},
    {"name": "Drexel University", "location": "Philadelphia, PA", "avg_gpa": 3.6, "acceptance_rate": 78.0, "rd": "2026-01-15", "portal": "https://drexel.edu/admissions"},
    {"name": "George Washington University", "location": "Washington, DC", "avg_gpa": 3.7, "acceptance_rate": 41.0, "rd": "2026-01-05", "ed": "2025-11-01", "portal": "https://gwu.edu/admissions"},
    {"name": "American University", "location": "Washington, DC", "avg_gpa": 3.6, "acceptance_rate": 41.0, "rd": "2026-01-15", "ed": "2025-11-15", "portal": "https://american.edu/admissions"},
    {"name": "Howard University", "location": "Washington, DC", "avg_gpa": 3.5, "acceptance_rate": 53.0, "rd": "2026-02-15", "ea": "2025-11-01", "portal": "https://howard.edu/admissions"},
    {"name": "Spelman College", "location": "Atlanta, GA", "avg_gpa": 3.6, "acceptance_rate": 29.0, "rd": "2026-02-01", "ea": "2025-11-01", "portal": "https://spelman.edu/admissions"},
]

@app.route('/api/colleges/search')
def search_colleges():
    query = request.args.get('q', '').lower()
    if len(query) < 2:
        return jsonify([])

    results = []
    for college in COLLEGE_DATABASE:
        if query in college['name'].lower():
            results.append(college)
            if len(results) >= 10:
                break

    return jsonify(results)

def calculate_chances(profile, college):
    """Calculate admission chances based on profile vs school stats"""
    if not profile or (not profile['gpa'] and not profile['sat_score'] and not profile['act_score']):
        return None

    score = 50  # Base score
    factors = []

    # GPA comparison
    if profile['gpa'] and college['avg_gpa']:
        gpa_diff = profile['gpa'] - college['avg_gpa']
        if gpa_diff >= 0.1:
            score += 15
            factors.append(('gpa', 'above', f"Your GPA ({profile['gpa']}) is above average ({college['avg_gpa']})"))
        elif gpa_diff >= -0.1:
            score += 5
            factors.append(('gpa', 'match', f"Your GPA ({profile['gpa']}) matches average ({college['avg_gpa']})"))
        elif gpa_diff >= -0.2:
            score -= 10
            factors.append(('gpa', 'below', f"Your GPA ({profile['gpa']}) is slightly below average ({college['avg_gpa']})"))
        else:
            score -= 20
            factors.append(('gpa', 'below', f"Your GPA ({profile['gpa']}) is below average ({college['avg_gpa']})"))

    # SAT comparison (estimate school SAT from acceptance rate if not available)
    if profile['sat_score']:
        # Estimate typical SAT based on acceptance rate
        if college['acceptance_rate']:
            rate = college['acceptance_rate']
            if rate <= 10:
                est_sat = 1520
            elif rate <= 20:
                est_sat = 1450
            elif rate <= 35:
                est_sat = 1380
            elif rate <= 50:
                est_sat = 1300
            else:
                est_sat = 1200

            sat_diff = profile['sat_score'] - est_sat
            if sat_diff >= 50:
                score += 15
                factors.append(('sat', 'above', f"Your SAT ({profile['sat_score']}) is above typical ({est_sat})"))
            elif sat_diff >= -30:
                score += 5
                factors.append(('sat', 'match', f"Your SAT ({profile['sat_score']}) is competitive ({est_sat} typical)"))
            elif sat_diff >= -80:
                score -= 10
                factors.append(('sat', 'below', f"Your SAT ({profile['sat_score']}) is below typical ({est_sat})"))
            else:
                score -= 20
                factors.append(('sat', 'below', f"Your SAT ({profile['sat_score']}) is well below typical ({est_sat})"))

    # Acceptance rate factor
    if college['acceptance_rate']:
        rate = college['acceptance_rate']
        if rate <= 10:
            score -= 15  # Very selective
        elif rate <= 20:
            score -= 5
        elif rate >= 50:
            score += 10  # Less selective

    # Clamp score
    score = max(5, min(95, score))

    # Determine category
    if score >= 70:
        category = 'likely'
        label = 'Likely'
        color = '#10b981'
    elif score >= 50:
        category = 'match'
        label = 'Match'
        color = '#3b82f6'
    elif score >= 30:
        category = 'reach'
        label = 'Reach'
        color = '#f59e0b'
    else:
        category = 'far_reach'
        label = 'Far Reach'
        color = '#ef4444'

    return {
        'score': score,
        'category': category,
        'label': label,
        'color': color,
        'factors': factors
    }

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/dashboard')
def dashboard():
    db = get_db()
    colleges = db.execute('SELECT * FROM colleges ORDER BY deadline_date ASC NULLS LAST').fetchall()
    profile = db.execute('SELECT * FROM profile WHERE id = 1').fetchone()

    # Stats
    total = len(colleges)
    by_status = {}
    for s, name, color, bg in STATUSES:
        count = len([c for c in colleges if c['status'] == s])
        by_status[s] = {'name': name, 'count': count, 'color': color, 'bg': bg}

    by_type = {}
    for t, name, color in SCHOOL_TYPES:
        count = len([c for c in colleges if c['type'] == t])
        by_type[t] = {'name': name, 'count': count, 'color': color}

    # Upcoming deadlines
    today = datetime.now().date()
    upcoming = [c for c in colleges if c['deadline_date'] and
                datetime.strptime(c['deadline_date'], '%Y-%m-%d').date() >= today and
                c['status'] not in ('submitted', 'accepted', 'rejected', 'waitlisted', 'withdrawn')]
    upcoming = sorted(upcoming, key=lambda x: x['deadline_date'])[:5]

    # Urgent deadlines (within 7 days)
    urgent = []
    for c in colleges:
        if c['deadline_date'] and c['status'] not in ('submitted', 'accepted', 'rejected', 'waitlisted', 'withdrawn'):
            deadline = datetime.strptime(c['deadline_date'], '%Y-%m-%d').date()
            days_left = (deadline - today).days
            if 0 <= days_left <= 7:
                urgent.append({'college': c, 'days': days_left})
    urgent = sorted(urgent, key=lambda x: x['days'])

    # Tasks due soon
    tasks = db.execute('''
        SELECT t.*, c.name as college_name FROM tasks t
        JOIN colleges c ON t.college_id = c.id
        WHERE t.is_done = 0
        ORDER BY t.due_date ASC NULLS LAST LIMIT 5
    ''').fetchall()

    # Calculate overall progress
    total_tasks = db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]
    done_tasks = db.execute('SELECT COUNT(*) FROM tasks WHERE is_done = 1').fetchone()[0]
    overall_progress = int((done_tasks / total_tasks * 100)) if total_tasks > 0 else 0

    # Generate insights
    insights = []

    # Profile insights
    if not profile or (not profile['gpa'] and not profile['sat_score']):
        insights.append({
            'type': 'warning',
            'icon': 'user',
            'title': 'Complete Your Profile',
            'message': 'Add your GPA and test scores to see personalized chances at each school.',
            'action': '/profile',
            'action_text': 'Add Stats'
        })

    # School balance insights
    if total > 0:
        safety_count = by_type.get('safety', {}).get('count', 0)
        reach_count = by_type.get('reach', {}).get('count', 0) + by_type.get('far_reach', {}).get('count', 0)

        if safety_count == 0 and total >= 3:
            insights.append({
                'type': 'warning',
                'icon': 'shield',
                'title': 'No Safety Schools',
                'message': 'Consider adding 2-3 safety schools to ensure you have options.',
                'action': '/school/add',
                'action_text': 'Add School'
            })
        elif reach_count > 0 and safety_count < 2 and total >= 5:
            insights.append({
                'type': 'info',
                'icon': 'lightbulb',
                'title': 'Balance Your List',
                'message': f'You have {reach_count} reach schools. Adding more safeties would strengthen your list.',
                'action': None,
                'action_text': None
            })

    # Deadline insights
    submitted_count = by_status.get('submitted', {}).get('count', 0)
    in_progress_count = by_status.get('in_progress', {}).get('count', 0)

    if len(urgent) > 0:
        insights.append({
            'type': 'urgent',
            'icon': 'clock',
            'title': f'{len(urgent)} Deadline{"s" if len(urgent) > 1 else ""} This Week',
            'message': f'You have applications due soon. Focus on completing them!',
            'action': '/timeline',
            'action_text': 'View Timeline'
        })

    if submitted_count > 0 and submitted_count == total:
        insights.append({
            'type': 'success',
            'icon': 'check',
            'title': 'All Applications Submitted!',
            'message': 'Great job! Now you wait for decisions. Good luck!',
            'action': None,
            'action_text': None
        })

    # Calculate chances for all schools
    school_chances = []
    if profile and (profile['gpa'] or profile['sat_score']):
        for c in colleges:
            chances = calculate_chances(profile, c)
            if chances:
                school_chances.append({'college': c, 'chances': chances})

    return render_template('dashboard.html',
                          colleges=colleges,
                          profile=profile,
                          stats={'total': total, 'by_status': by_status, 'by_type': by_type},
                          upcoming=upcoming,
                          urgent=urgent,
                          tasks=tasks,
                          today=today,
                          insights=insights,
                          overall_progress=overall_progress,
                          school_chances=school_chances,
                          statuses=STATUSES,
                          school_types=SCHOOL_TYPES)

@app.route('/schools')
def schools():
    db = get_db()
    colleges = db.execute('SELECT * FROM colleges ORDER BY deadline_date ASC NULLS LAST').fetchall()

    # Get task counts for each college
    task_counts = {}
    for college in colleges:
        total = db.execute('SELECT COUNT(*) FROM tasks WHERE college_id = ?', (college['id'],)).fetchone()[0]
        done = db.execute('SELECT COUNT(*) FROM tasks WHERE college_id = ? AND is_done = 1', (college['id'],)).fetchone()[0]
        task_counts[college['id']] = {'total': total, 'done': done}

    return render_template('schools.html',
                          colleges=colleges,
                          task_counts=task_counts,
                          statuses=STATUSES,
                          deadline_types=DEADLINE_TYPES,
                          school_types=SCHOOL_TYPES)

@app.route('/school/add', methods=['GET', 'POST'])
def add_school():
    if request.method == 'POST':
        db = get_db()
        db.execute('''
            INSERT INTO colleges (name, location, type, deadline_type, deadline_date, status, avg_gpa, acceptance_rate, portal_url, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form['name'],
            request.form.get('location', ''),
            request.form.get('type', 'reach'),
            request.form.get('deadline_type', 'rd'),
            request.form.get('deadline_date') or None,
            request.form.get('status', 'researching'),
            request.form.get('avg_gpa') or None,
            request.form.get('acceptance_rate') or None,
            request.form.get('portal_url', ''),
            request.form.get('notes', ''),
        ))
        db.commit()

        college_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Add default tasks
        default_tasks = [
            ('Complete Application', 'application'),
            ('Request Transcript', 'document'),
            ('Send Test Scores', 'document'),
            ('Counselor Recommendation', 'recommendation'),
            ('Teacher Recommendation', 'recommendation'),
            ('Submit Application Fee', 'financial'),
        ]
        for task_name, category in default_tasks:
            db.execute('INSERT INTO tasks (college_id, name, category) VALUES (?, ?, ?)',
                      (college_id, task_name, category))
        db.commit()

        return redirect(url_for('school_detail', id=college_id))

    return render_template('add_school.html',
                          statuses=STATUSES,
                          deadline_types=DEADLINE_TYPES,
                          school_types=SCHOOL_TYPES)

@app.route('/school/<int:id>')
def school_detail(id):
    db = get_db()
    college = db.execute('SELECT * FROM colleges WHERE id = ?', (id,)).fetchone()
    if not college:
        return redirect(url_for('schools'))

    tasks = db.execute('SELECT * FROM tasks WHERE college_id = ? ORDER BY is_done ASC, category', (id,)).fetchall()
    essays = db.execute('SELECT * FROM essays WHERE college_id = ?', (id,)).fetchall()
    profile = db.execute('SELECT * FROM profile WHERE id = 1').fetchone()

    done_tasks = len([t for t in tasks if t['is_done']])
    total_tasks = len(tasks)
    progress = int((done_tasks / total_tasks * 100)) if total_tasks > 0 else 0

    # Calculate chances
    chances = calculate_chances(profile, college)

    return render_template('school_detail.html',
                          college=college,
                          tasks=tasks,
                          essays=essays,
                          progress=progress,
                          chances=chances,
                          profile=profile,
                          statuses=STATUSES,
                          deadline_types=DEADLINE_TYPES,
                          school_types=SCHOOL_TYPES)

@app.route('/school/<int:id>/update', methods=['POST'])
def update_school(id):
    db = get_db()
    db.execute('''
        UPDATE colleges SET name=?, location=?, type=?, deadline_type=?, deadline_date=?,
        status=?, avg_gpa=?, acceptance_rate=?, portal_url=?, notes=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    ''', (
        request.form['name'],
        request.form.get('location', ''),
        request.form.get('type', 'reach'),
        request.form.get('deadline_type', 'rd'),
        request.form.get('deadline_date') or None,
        request.form.get('status', 'researching'),
        request.form.get('avg_gpa') or None,
        request.form.get('acceptance_rate') or None,
        request.form.get('portal_url', ''),
        request.form.get('notes', ''),
        id
    ))
    db.commit()
    return redirect(url_for('school_detail', id=id))

@app.route('/school/<int:id>/delete', methods=['POST'])
def delete_school(id):
    db = get_db()
    db.execute('DELETE FROM tasks WHERE college_id = ?', (id,))
    db.execute('DELETE FROM essays WHERE college_id = ?', (id,))
    db.execute('DELETE FROM colleges WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('schools'))

@app.route('/school/<int:id>/status', methods=['POST'])
def update_status(id):
    db = get_db()
    db.execute('UPDATE colleges SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?',
               (request.form['status'], id))
    db.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    return redirect(request.referrer or url_for('schools'))

@app.route('/task/<int:id>/toggle', methods=['POST'])
def toggle_task(id):
    db = get_db()
    task = db.execute('SELECT * FROM tasks WHERE id = ?', (id,)).fetchone()
    if task:
        new_done = 0 if task['is_done'] else 1
        db.execute('UPDATE tasks SET is_done = ? WHERE id = ?', (new_done, id))
        db.commit()

        # Check if all tasks are done - auto-update status to submitted
        college_id = task['college_id']
        total_tasks = db.execute('SELECT COUNT(*) FROM tasks WHERE college_id = ?', (college_id,)).fetchone()[0]
        done_tasks = db.execute('SELECT COUNT(*) FROM tasks WHERE college_id = ? AND is_done = 1', (college_id,)).fetchone()[0]

        status_changed = None
        if total_tasks > 0 and done_tasks == total_tasks:
            # All tasks complete - set status to submitted
            db.execute('UPDATE colleges SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status NOT IN (?, ?, ?, ?, ?)',
                      ('submitted', college_id, 'submitted', 'accepted', 'rejected', 'waitlisted', 'withdrawn'))
            db.commit()
            status_changed = 'submitted'

        return jsonify({'success': True, 'done': bool(new_done), 'status_changed': status_changed})
    return jsonify({'success': False}), 404

@app.route('/school/<int:college_id>/task/add', methods=['POST'])
def add_task(college_id):
    db = get_db()
    db.execute('INSERT INTO tasks (college_id, name, category, due_date) VALUES (?, ?, ?, ?)',
               (college_id, request.form['name'], request.form.get('category', 'general'),
                request.form.get('due_date') or None))
    db.commit()
    return redirect(url_for('school_detail', id=college_id))

@app.route('/task/<int:id>/delete', methods=['POST'])
def delete_task(id):
    db = get_db()
    task = db.execute('SELECT college_id FROM tasks WHERE id = ?', (id,)).fetchone()
    if task:
        db.execute('DELETE FROM tasks WHERE id = ?', (id,))
        db.commit()
    return redirect(url_for('school_detail', id=task['college_id']) if task else url_for('schools'))

@app.route('/school/<int:college_id>/essay/add', methods=['POST'])
def add_essay(college_id):
    db = get_db()
    db.execute('INSERT INTO essays (college_id, title, prompt, word_limit, status) VALUES (?, ?, ?, ?, ?)',
               (college_id, request.form['title'], request.form.get('prompt', ''),
                request.form.get('word_limit') or None, request.form.get('status', 'not_started')))
    db.commit()
    return redirect(url_for('school_detail', id=college_id))

@app.route('/essay/<int:id>/update', methods=['POST'])
def update_essay(id):
    db = get_db()
    essay = db.execute('SELECT college_id FROM essays WHERE id = ?', (id,)).fetchone()
    if essay:
        db.execute('UPDATE essays SET status=? WHERE id=?', (request.form['status'], id))
        db.commit()
    return redirect(url_for('school_detail', id=essay['college_id']) if essay else url_for('schools'))

@app.route('/essay/<int:id>/delete', methods=['POST'])
def delete_essay(id):
    db = get_db()
    essay = db.execute('SELECT college_id FROM essays WHERE id = ?', (id,)).fetchone()
    if essay:
        db.execute('DELETE FROM essays WHERE id = ?', (id,))
        db.commit()
    return redirect(url_for('school_detail', id=essay['college_id']) if essay else url_for('schools'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    db = get_db()
    if request.method == 'POST':
        db.execute('UPDATE profile SET gpa=?, sat_score=?, act_score=? WHERE id=1',
                   (request.form.get('gpa') or None,
                    request.form.get('sat_score') or None,
                    request.form.get('act_score') or None))
        db.commit()
        return redirect(url_for('dashboard'))

    profile = db.execute('SELECT * FROM profile WHERE id = 1').fetchone()
    return render_template('profile.html', profile=profile)

@app.route('/timeline')
def timeline():
    db = get_db()
    colleges = db.execute('''
        SELECT * FROM colleges
        WHERE deadline_date IS NOT NULL
        ORDER BY deadline_date ASC
    ''').fetchall()

    # Group by month
    months = {}
    for c in colleges:
        date = datetime.strptime(c['deadline_date'], '%Y-%m-%d')
        key = date.strftime('%B %Y')
        if key not in months:
            months[key] = []
        months[key].append(c)

    return render_template('timeline.html', months=months, statuses=STATUSES, today=datetime.now().date())

@app.template_filter('days_until')
def days_until(date_str):
    if not date_str:
        return None
    try:
        deadline = datetime.strptime(str(date_str), '%Y-%m-%d').date()
        return (deadline - datetime.now().date()).days
    except:
        return None

@app.template_filter('status_info')
def status_info(status):
    for s, name, color, bg in STATUSES:
        if s == status:
            return {'name': name, 'color': color, 'bg': bg}
    return {'name': status, 'color': '#6b7280', 'bg': 'bg-gray-100'}

@app.template_filter('type_info')
def type_info(type_):
    for t, name, color in SCHOOL_TYPES:
        if t == type_:
            return {'name': name, 'color': color}
    return {'name': type_, 'color': '#6b7280'}

@app.template_filter('deadline_info')
def deadline_info(deadline_type):
    for d, name, typical in DEADLINE_TYPES:
        if d == deadline_type:
            return {'name': name, 'typical': typical}
    return {'name': deadline_type, 'typical': ''}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
