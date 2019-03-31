import requests
import sys
import os
from io import StringIO
import csv
import json

URL_AUTH = '/api/v0/authentication'
URL_COURSES = '/api/v0/courses'
REPORT_FILENAME = 'report.csv'

class Inginious:
    def __init__(self, url, user, password, bonus=[]):
        self.base_url = url
        self.user = user
        self.password = password
        self.bonus_tasks = bonus
        cook = self.login()
        self.session = dict(webpy_session_id=cook)
        
    def login(self):
        r = requests.post(self.base_url+URL_AUTH, data = {'auth_method_id':'0', 'login':self.user, 'password':self.password})
        return r.cookies['webpy_session_id']
    
    def get_courses(self):
        r = requests.get(self.base_url+URL_COURSES, cookies=self.session)
        j = json.loads(r.text)
        return [course['id'] for course in j if course['is_registered']]
    
    def get_grades_url(self, course):
        return self.base_url+'/admin/'+course+'/students?csv'
    
    def get_grades(self, course, all_users=False):
        r = requests.get(self.get_grades_url(course), cookies=self.session)
        f = StringIO(r.text)
        reader = csv.DictReader(f, delimiter=',')
        return [student for student in reader if all_users or student['id'][0] == 's']
    
    def get_all_grades(self, all_users=False):
        courses = self.get_courses()
        return {course:self.get_grades(course, all_users) for course in courses}

    def generate_grades_report(self, all_users=False):
        mylist = []
        data = self.get_all_grades(all_users)
        for course in data:
            print('Class', course + ':')
            for student in data[course]:
                all_tasks = [task for task in student.keys() if 'task_grades[' in task]
                nonbonus_tasks = [task for task in all_tasks for bonus in self.bonus_tasks if bonus not in task]
                bonus_tasks = [task for task in all_tasks for bonus in self.bonus_tasks if bonus in task]
                grades = [float(student[task]) if len(student[task]) > 0 else 0.0 for task in nonbonus_tasks]
                print(student['id'], student['realname'], round(sum(grades)/len(grades)))
                mylist.append(','.join([course, student['id'], student['realname'], str(round(sum(grades)/len(grades)))]))
            print()

        with open(REPORT_FILENAME,'w', encoding="utf-8") as f:
            f.write('\n'.join(mylist))

def main():
    if len(sys.argv) > 1:
        ing_url = sys.argv[1]
        ing_user = sys.argv[2]
        ing_pass = sys.argv[3]
    else:
        ing_url = os.environ['ING_URL']
        ing_user = os.environ['ING_USER']
        ing_pass = os.environ['ING_PASS']
    ing = Inginious(ing_url, ing_user, ing_pass, bonus=['01-04-03','06-02-04', '08-02-04', '09-03-02'])
    ing.generate_grades_report()


if __name__ == '__main__':
    main()

