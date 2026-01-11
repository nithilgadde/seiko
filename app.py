import os
from flask import Flask, render_template, request, jsonify

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.secret_key = os.environ.get('SECRET_KEY', 'seiko-2024')

# College database for autocomplete
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

# API endpoint for college autocomplete
@app.route('/api/colleges/search')
def search_colleges():
    query = request.args.get('q', '').lower()
    if len(query) < 2:
        return jsonify([])
    results = [c for c in COLLEGE_DATABASE if query in c['name'].lower()][:10]
    return jsonify(results)

# Simple routes - all data is handled client-side via localStorage
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/schools')
def schools():
    return render_template('schools.html')

@app.route('/school/add')
def add_school():
    return render_template('add_school.html')

@app.route('/school/<int:college_id>')
def school_detail(college_id):
    return render_template('school_detail.html')

@app.route('/timeline')
def timeline():
    return render_template('timeline.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
