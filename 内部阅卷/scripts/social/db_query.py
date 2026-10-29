#!/usr/bin/env python3
"""
社招阅卷 - 数据库查询工具
用于连接数据库获取正确答案
"""

import pymysql
import json
import sys

class ExamDatabase:
    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        
    def connect(self):
        """连接数据库"""
        try:
            self.conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4'
            )
            print(f"✅ 成功连接到数据库 {self.host}:{self.port}/{self.database}")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
            
    def execute_query(self, sql):
        """执行SQL查询"""
        if not self.conn:
            if not self.connect():
                return None
                
        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql)
                results = cursor.fetchall()
                return results
        except Exception as e:
            print(f"❌ SQL执行失败: {e}")
            return None
            
    def get_students_with_score_above(self, lesson_name, score_threshold):
        """查询某课程成绩大于指定分数的学生"""
        sql = f"""
        SELECT s.student_name, sc.score, c.class_name
        FROM student s
        JOIN score sc ON s.student_id = sc.student_id
        JOIN lesson l ON sc.lesson_id = l.lesson_id
        JOIN class c ON s.classes_id = c.class_id
        WHERE l.lesson_name = '{lesson_name}'
        AND sc.score > {score_threshold}
        ORDER BY sc.score DESC
        """
        return self.execute_query(sql)
        
    def get_top_n_per_class_per_lesson(self, n=2):
        """查询每个班级每门课程成绩前N名"""
        sql = f"""
        SELECT c.class_name, l.lesson_name, s.student_name, sc.score
        FROM student s
        JOIN score sc ON s.student_id = sc.student_id
        JOIN lesson l ON sc.lesson_id = l.lesson_id
        JOIN class c ON s.classes_id = c.class_id
        WHERE (
            SELECT COUNT(*)
            FROM score sc2
            JOIN student s2 ON sc2.student_id = s2.student_id
            WHERE sc2.lesson_id = sc.lesson_id
            AND s2.classes_id = s.classes_id
            AND sc2.score > sc.score
        ) < {n}
        ORDER BY c.class_name, l.lesson_name, sc.score DESC
        """
        return self.execute_query(sql)
        
    def get_students_logged_consecutive_days(self, days=3):
        """查询连续登录指定天数的学生"""
        sql = f"""
        SELECT DISTINCT s.student_name, c.class_name
        FROM student s
        JOIN login_student ls ON s.student_id = ls.student_id
        JOIN class c ON s.classes_id = c.class_id
        WHERE s.student_id IN (
            SELECT ls1.student_id
            FROM login_student ls1
            JOIN login_student ls2 ON ls1.student_id = ls2.student_id
                AND DATEDIFF(ls2.login_date, ls1.login_date) = 1
            JOIN login_student ls3 ON ls1.student_id = ls3.student_id
                AND DATEDIFF(ls3.login_date, ls2.login_date) = 1
            GROUP BY ls1.student_id
        )
        """
        return self.execute_query(sql)
        
    def get_student_scores(self, student_name):
        """查询学生所有课程成绩"""
        sql = f"""
        SELECT l.lesson_name, sc.score
        FROM student s
        JOIN score sc ON s.student_id = sc.student_id
        JOIN lesson l ON sc.lesson_id = l.lesson_id
        WHERE s.student_name = '{student_name}'
        ORDER BY l.lesson_name
        """
        return self.execute_query(sql)
        
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("✅ 数据库连接已关闭")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python db_query.py <命令> [参数...]")
        print("命令:")
        print("  students_above <课程名> <分数阈值>")
        print("  top_n <N>")
        print("  consecutive_login <天数>")
        print("  student_scores <学生姓名>")
        return
        
    # 默认数据库配置
    db_config = {
        'host': 'demo.egova.com.cn',
        'port': 18260,
        'user': 'root',
        'password': 'eGova#2020',
        'database': 'school'
    }
    
    db = ExamDatabase(**db_config)
    
    if not db.connect():
        return
        
    command = sys.argv[1]
    
    try:
        if command == 'students_above':
            if len(sys.argv) < 4:
                print("用法: students_above <课程名> <分数阈值>")
                return
            lesson_name = sys.argv[2]
            score_threshold = float(sys.argv[3])
            results = db.get_students_with_score_above(lesson_name, score_threshold)
            print(json.dumps(results, ensure_ascii=False, indent=2))
            
        elif command == 'top_n':
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 2
            results = db.get_top_n_per_class_per_lesson(n)
            print(json.dumps(results, ensure_ascii=False, indent=2))
            
        elif command == 'consecutive_login':
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            results = db.get_students_logged_consecutive_days(days)
            print(json.dumps(results, ensure_ascii=False, indent=2))
            
        elif command == 'student_scores':
            if len(sys.argv) < 3:
                print("用法: student_scores <学生姓名>")
                return
            student_name = sys.argv[2]
            results = db.get_student_scores(student_name)
            print(json.dumps(results, ensure_ascii=False, indent=2))
            
        else:
            print(f"未知命令: {command}")
            
    finally:
        db.close()


if __name__ == '__main__':
    main()
