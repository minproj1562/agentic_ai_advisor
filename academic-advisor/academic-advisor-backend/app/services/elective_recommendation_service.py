#academic-advisor-backend/app/services/elective_recommendation_service.py
class ElectiveRecommender:
    def __init__(self):
        self.sem4_subjects = [
            'Database Management System',
            'Digital Logic and Design',
            'Computer Organization and Architecture',
            'Operating System',
            'Data Structures and Algorithms',
            'Computer Networks',
            'Microprocessor and Embedded Systems',
            'C',
            'Python',
            'Java'
        ]
        
        self.sem5_subjects = self.sem4_subjects + [
            'Automata Theory',
            'Full Stack Development (FSDL)',
            'Flutter',
            'Artificial Intelligence',
            'Internet of Things (IoT)'
        ]
        
        self.interest_areas = [
            'Artificial Intelligence & Machine Learning',
            'Mobile & IoT Development',
            'Web Development',
            'Data Science & Analytics',
            'Cloud & Distributed Systems',
            'Network & Wireless Systems'
        ]
        
        # Subject relevance weights for each elective
        self.ml_relevant = {
            'Python': 3.0,
            'Data Structures and Algorithms': 2.5,
            'Artificial Intelligence': 3.5,
            'Database Management System': 1.5,
            'Java': 1.0
        }
        
        self.wt_relevant = {
            'Computer Networks': 3.5,
            'Microprocessor and Embedded Systems': 3.0,
            'Internet of Things (IoT)': 3.5,
            'Operating System': 2.0,
            'C': 2.0
        }
        
        self.dwm_relevant = {
            'Database Management System': 3.5,
            'Data Structures and Algorithms': 2.5,
            'Python': 2.0,
            'Artificial Intelligence': 2.0,
            'Java': 1.5
        }
        
        self.ccs_relevant = {
            'Computer Networks': 3.0,
            'Operating System': 2.5,
            'Database Management System': 2.0,
            'Full Stack Development (FSDL)': 3.0,
            'Java': 2.0,
            'Python': 1.5
        }
        
        # Skill requirements for each elective
        self.skill_requirements = {
            'ML': [
                {'subject': 'Python', 'importance': 'Critical'},
                {'subject': 'Data Structures and Algorithms', 'importance': 'High'},
                {'subject': 'Artificial Intelligence', 'importance': 'High'},
                {'subject': 'Database Management System', 'importance': 'Medium'}
            ],
            'WT': [
                {'subject': 'Computer Networks', 'importance': 'Critical'},
                {'subject': 'Microprocessor and Embedded Systems', 'importance': 'High'},
                {'subject': 'Internet of Things (IoT)', 'importance': 'High'},
                {'subject': 'C', 'importance': 'Medium'}
            ],
            'DWM': [
                {'subject': 'Database Management System', 'importance': 'Critical'},
                {'subject': 'Data Structures and Algorithms', 'importance': 'High'},
                {'subject': 'Python', 'importance': 'Medium'},
                {'subject': 'Artificial Intelligence', 'importance': 'Medium'}
            ],
            'CCS': [
                {'subject': 'Computer Networks', 'importance': 'High'},
                {'subject': 'Operating System', 'importance': 'High'},
                {'subject': 'Database Management System', 'importance': 'Medium'},
                {'subject': 'Full Stack Development (FSDL)', 'importance': 'High'}
            ]
        }
    
    def get_subjects_for_semester(self, semester):
        """Return list of subjects for the given semester"""
        return self.sem4_subjects if semester == 4 else self.sem5_subjects
    
    def calculate_weighted_score(self, marks, relevant_subjects):
        """Calculate weighted average score based on subject relevance"""
        score = 0
        weight_sum = 0
        
        for subject, weight in relevant_subjects.items():
            if subject in marks:
                score += marks[subject] * weight
                weight_sum += weight
        
        return score / weight_sum if weight_sum > 0 else 0
    
    def calculate_interest_score(self, interests, elective):
        """Calculate interest score for an elective"""
        interest_mapping = {
            'ML': [
                ('Artificial Intelligence & Machine Learning', 2.0),
                ('Data Science & Analytics', 1.5)
            ],
            'WT': [
                ('Network & Wireless Systems', 2.0),
                ('Mobile & IoT Development', 1.5)
            ],
            'DWM': [
                ('Data Science & Analytics', 2.0),
                ('Artificial Intelligence & Machine Learning', 1.0)
            ],
            'CCS': [
                ('Cloud & Distributed Systems', 2.0),
                ('Web Development', 1.5)
            ]
        }
        
        score = 0
        for area, weight in interest_mapping[elective]:
            score += interests.get(area, 3) * weight
        
        return score
    
    def analyze_skill_gaps(self, elective, marks, threshold=60):
        """Identify skill gaps for the recommended elective"""
        gaps = []
        
        for req in self.skill_requirements[elective]:
            subject = req['subject']
            importance = req['importance']
            mark = marks.get(subject, 0)
            
            if mark < threshold and mark > 0:
                gap = {
                    'subject': subject,
                    'importance': importance,
                    'current_level': mark,
                    'gap': threshold - mark,
                    'status': 'Needs Major Improvement' if mark < 40 else 'Needs Improvement'
                }
                gaps.append(gap)
        
        return gaps
    
    def generate_marks_reasoning(self, elective, marks, avg_score, relevant_subjects):
        """Generate reasoning based on marks performance"""
        strong_subjects = []
        weak_subjects = []
        
        for subject in relevant_subjects.keys():
            mark = marks.get(subject, 0)
            if mark >= 70:
                strong_subjects.append(subject)
            elif 0 < mark < 60:
                weak_subjects.append(subject)
        
        elective_names = {
            'ML': 'Machine Learning',
            'WT': 'Wireless Technology',
            'DWM': 'Data Warehouse and Data Mining',
            'CCS': 'Cloud Computing Services'
        }
        
        reasoning = f"Your performance in {elective}-related subjects shows an average of {avg_score:.1f}%. "
        
        if strong_subjects:
            reasoning += f"You have strong foundations in {', '.join(strong_subjects)} with marks above 70%. "
        
        if weak_subjects:
            reasoning += f"Areas needing attention include {', '.join(weak_subjects)}. "
        
        reasoning += f"This makes you well-suited for {elective_names[elective]}."
        
        return reasoning
    
    def generate_interest_reasoning(self, elective, interests):
        """Generate reasoning based on interest alignment"""
        interest_mapping = {
            'ML': ['Artificial Intelligence & Machine Learning', 'Data Science & Analytics'],
            'WT': ['Network & Wireless Systems', 'Mobile & IoT Development'],
            'DWM': ['Data Science & Analytics', 'Artificial Intelligence & Machine Learning'],
            'CCS': ['Cloud & Distributed Systems', 'Web Development']
        }
        
        elective_names = {
            'ML': 'Machine Learning',
            'WT': 'Wireless Technology',
            'DWM': 'Data Warehouse and Data Mining',
            'CCS': 'Cloud Computing Services'
        }
        
        relevant_interests = interest_mapping[elective]
        high_interests = [area for area in relevant_interests if interests.get(area, 3) >= 4]
        
        if high_interests:
            return f"Your high interest in {' and '.join(high_interests)} aligns perfectly with {elective_names[elective]}, which will allow you to explore these areas in depth."
        else:
            return f"{elective_names[elective]} matches your overall interest profile and will help you develop skills in {relevant_interests[0].lower()}."
    
    def recommend(self, semester, marks, interests):
        """
        Main recommendation function
        
        Args:
            semester (int): Current semester (4 or 5)
            marks (dict): Dictionary of subject names and marks
            interests (dict): Dictionary of interest areas and ratings (1-5)
        
        Returns:
            dict: Recommendation with reasoning and analysis
        """
        # Calculate weighted averages for each elective
        ml_avg = self.calculate_weighted_score(marks, self.ml_relevant)
        wt_avg = self.calculate_weighted_score(marks, self.wt_relevant)
        dwm_avg = self.calculate_weighted_score(marks, self.dwm_relevant)
        ccs_avg = self.calculate_weighted_score(marks, self.ccs_relevant)
        
        # Calculate interest scores
        ml_interest = self.calculate_interest_score(interests, 'ML')
        wt_interest = self.calculate_interest_score(interests, 'WT')
        dwm_interest = self.calculate_interest_score(interests, 'DWM')
        ccs_interest = self.calculate_interest_score(interests, 'CCS')
        
        # Combine marks (70%) and interests (30%)
        final_scores = {
            'ML': ml_avg * 0.7 + ml_interest * 0.3,
            'WT': wt_avg * 0.7 + wt_interest * 0.3,
            'DWM': dwm_avg * 0.7 + dwm_interest * 0.3,
            'CCS': ccs_avg * 0.7 + ccs_interest * 0.3
        }
        
        # Determine best pair
        pair1_score = max(final_scores['ML'], final_scores['WT'])
        pair2_score = max(final_scores['DWM'], final_scores['CCS'])
        
        if pair1_score >= pair2_score:
            recommended_pair = 'Pair 1'
            recommended_elective = 'ML' if final_scores['ML'] >= final_scores['WT'] else 'WT'
        else:
            recommended_pair = 'Pair 2'
            recommended_elective = 'DWM' if final_scores['DWM'] >= final_scores['CCS'] else 'CCS'
        
        # Get the relevant subjects and average for the recommended elective
        relevant_map = {
            'ML': (self.ml_relevant, ml_avg),
            'WT': (self.wt_relevant, wt_avg),
            'DWM': (self.dwm_relevant, dwm_avg),
            'CCS': (self.ccs_relevant, ccs_avg)
        }
        
        relevant_subjects, avg_score = relevant_map[recommended_elective]
        
        # Analyze skill gaps
        skill_gaps = self.analyze_skill_gaps(recommended_elective, marks)
        
        # Generate reasoning
        marks_reasoning = self.generate_marks_reasoning(
            recommended_elective, marks, avg_score, relevant_subjects
        )
        interest_reasoning = self.generate_interest_reasoning(recommended_elective, interests)
        
        elective_names = {
            'ML': 'Machine Learning',
            'WT': 'Wireless Technology',
            'DWM': 'Data Warehouse and Data Mining',
            'CCS': 'Cloud Computing Services'
        }
        
        return {
            'elective': elective_names[recommended_elective],
            'code': recommended_elective,
            'pair': recommended_pair,
            'marks_reasoning': marks_reasoning,
            'interest_reasoning': interest_reasoning,
            'skill_gaps': skill_gaps,
            'scores': final_scores
        }
    
    def print_recommendation(self, recommendation):
        """Print the recommendation in a formatted way"""
        print("\n" + "="*70)
        print("ELECTIVE RECOMMENDATION SYSTEM")
        print("="*70)
        
        print(f"\n🎯 RECOMMENDED ELECTIVE: {recommendation['elective']}")
        print(f"   From: {recommendation['pair']}")
        
        print(f"\n📈 PERFORMANCE ANALYSIS:")
        print(f"   {recommendation['marks_reasoning']}")
        
        print(f"\n💡 INTEREST ALIGNMENT:")
        print(f"   {recommendation['interest_reasoning']}")
        
        print(f"\n⚠️  SKILL GAP ANALYSIS:")
        if not recommendation['skill_gaps']:
            print("   ✅ Excellent! You have strong foundations in all key areas.")
        else:
            for gap in recommendation['skill_gaps']:
                print(f"\n   Subject: {gap['subject']}")
                print(f"   Importance: {gap['importance']}")
                print(f"   Current Level: {gap['current_level']}%")
                print(f"   Gap: {gap['gap']} marks")
                print(f"   Status: {gap['status']}")
        
        print("\n" + "="*70)


# Example usage
if __name__ == "__main__":
    # Create recommender instance
    recommender = ElectiveRecommender()
    
    # Example 1: Semester 4 student
    print("\n### EXAMPLE 1: SEMESTER 4 STUDENT ###")
    
    semester = 4
    marks = {
        'Database Management System': 75,
        'Digital Logic and Design': 68,
        'Computer Organization and Architecture': 72,
        'Operating System': 70,
        'Data Structures and Algorithms': 80,
        'Computer Networks': 65,
        'Microprocessor and Embedded Systems': 60,
        'C': 70,
        'Python': 85,
        'Java': 78
    }
    
    interests = {
        'Artificial Intelligence & Machine Learning': 5,
        'Mobile & IoT Development': 3,
        'Web Development': 3,
        'Data Science & Analytics': 4,
        'Cloud & Distributed Systems': 2,
        'Network & Wireless Systems': 3
    }
    
    recommendation = recommender.recommend(semester, marks, interests)
    recommender.print_recommendation(recommendation)
    
    # Example 2: Semester 5 student
    print("\n\n### EXAMPLE 2: SEMESTER 5 STUDENT ###")
    
    semester = 5
    marks = {
        'Database Management System': 72,
        'Digital Logic and Design': 70,
        'Computer Organization and Architecture': 68,
        'Operating System': 75,
        'Data Structures and Algorithms': 70,
        'Computer Networks': 82,
        'Microprocessor and Embedded Systems': 78,
        'C': 80,
        'Python': 65,
        'Java': 70,
        'Automata Theory': 68,
        'Full Stack Development (FSDL)': 60,
        'Flutter': 65,
        'Artificial Intelligence': 62,
        'Internet of Things (IoT)': 85
    }
    
    interests = {
        'Artificial Intelligence & Machine Learning': 3,
        'Mobile & IoT Development': 5,
        'Web Development': 3,
        'Data Science & Analytics': 2,
        'Cloud & Distributed Systems': 3,
        'Network & Wireless Systems': 5
    }
    
    recommendation = recommender.recommend(semester, marks, interests)
    recommender.print_recommendation(recommendation)
    
    # Interactive mode
    print("\n\n### INTERACTIVE MODE ###")
    print("\nWould you like to enter your own data? (This is just an example)")
    print("To use this script interactively, modify the marks and interests dictionaries above.")