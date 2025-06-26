import os
import json
import time
import random
import pandas as pd
import requests
import matplotlib.pyplot as plt
from datetime import datetime
from collections import Counter
from bs4 import BeautifulSoup
from urllib.parse import quote
from fake_useragent import UserAgent

# Configuration
CONFIG_FILE = "skill_config.json"
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

# Default configuration
DEFAULT_CONFIG = {
    "user_skills": ["Python", "Data Analysis", "Machine Learning"],
    "job_roles": ["Data Scientist", "Machine Learning Engineer", "AI Researcher"],
    "location": "United States",
    "max_pages": 3,
    "platforms": {
        "Coursera": "https://www.coursera.org/search?query={}",
        "edX": "https://www.edx.org/search?q={}",
        "YouTube": "https://www.youtube.com/results?search_query={}",
        "Kaggle": "https://www.kaggle.com/search?q={}",
        "freeCodeCamp": "https://www.freecodecamp.org/news/search/?query={}"
    }
}

# Initialize user agent
ua = UserAgent()

def load_config():
    """Load or create configuration file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG

def scrape_linkedin_jobs(job_roles, location, max_pages):
    """Scrape job data from LinkedIn"""
    job_data = []
    
    for job_role in job_roles:
        print(f"Scraping jobs for: {job_role}")
        
        for page in range(max_pages):
            # Format search URL
            search_query = f"{job_role} {location}"
            encoded_query = quote(search_query)
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_query}&location={location}&start={page * 25}"
            
            try:
                headers = {'User-Agent': ua.random}
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                jobs = soup.find_all('li')
                
                if not jobs:
                    break
                
                for job in jobs:
                    try:
                        # Extract job details
                        job_title = job.find('h3', class_='base-search-card__title').text.strip()
                        company = job.find('h4', class_='base-search-card__subtitle').text.strip()
                        location = job.find('span', class_='job-search-card__location').text.strip()
                        meta = job.find('div', class_='base-search-card__metadata')
                        date = meta.find('time')['datetime'] if meta.find('time') else "N/A"
                        job_url = job.find('a', class_='base-card__full-link')['href']
                        
                        # Get job description
                        desc_response = requests.get(job_url, headers=headers, timeout=5)
                        desc_soup = BeautifulSoup(desc_response.text, 'html.parser')
                        description = desc_soup.find('div', class_='description__text').get_text(separator=' ', strip=True) if desc_soup.find('div', class_='description__text') else ""
                        
                        # Extract skills from description
                        skills = extract_skills_from_text(description)
                        
                        job_data.append({
                            'title': job_title,
                            'company': company,
                            'location': location,
                            'date': date,
                            'skills': skills,
                            'url': job_url
                        })
                        
                        # Random delay to avoid blocking
                        time.sleep(random.uniform(1, 2))
                        
                    except Exception as e:
                        print(f"  Error processing job: {str(e)}")
                        continue
                
                print(f"  Page {page+1} complete")
                time.sleep(random.uniform(2, 3))  # Delay between pages
                
            except Exception as e:
                print(f"Error scraping page: {str(e)}")
                break
    
    return job_data

def extract_skills_from_text(text):
    """Extract skills using keyword matching"""
    tech_skills = [
        'python', 'r', 'java', 'c++', 'javascript', 'sql', 'scala', 
        'machine learning', 'deep learning', 'ai', 'artificial intelligence',
        'tensorflow', 'pytorch', 'keras', 'scikit-learn', 
        'data analysis', 'data visualization', 'statistics', 
        'big data', 'hadoop', 'spark', 'hive', 
        'cloud', 'aws', 'azure', 'gcp', 
        'docker', 'kubernetes', 
        'sql', 'nosql', 'mongodb', 'cassandra', 
        'tableau', 'power bi', 'matplotlib', 'seaborn', 
        'nlp', 'computer vision', 'reinforcement learning',
        'git', 'agile', 'scrum', 
        'excel', 'pandas', 'numpy', 'dask',
        'linux', 'bash', 'api', 'rest', 'graphql',
        'spark', 'hadoop', 'kafka', 'airflow',
        'mlops', 'ci/cd', 'jenkins', 'github actions',
        'tableau', 'powerbi', 'looker', 'redshift',
        'snowflake', 'bigquery', 'postgresql', 'mysql'
    ]
    
    soft_skills = [
        'communication', 'problem solving', 'teamwork', 
        'leadership', 'time management', 'critical thinking',
        'adaptability', 'creativity', 'emotional intelligence',
        'collaboration', 'negotiation', 'conflict resolution'
    ]
    
    found_skills = []
    text_lower = text.lower()
    
    for skill in tech_skills + soft_skills:
        if skill in text_lower:
            found_skills.append(skill.title())
    
    return list(set(found_skills))

def analyze_skill_gap(user_skills, job_market_data):
    """Analyze gap between user skills and market demands"""
    # Aggregate required skills from job market
    all_required_skills = []
    for job in job_market_data:
        all_required_skills.extend(job['skills'])
    
    skill_frequency = Counter(all_required_skills)
    total_jobs = len(job_market_data)
    
    # Calculate skill demand percentage
    skill_demand = {skill: (count/total_jobs)*100 for skill, count in skill_frequency.items()}
    
    # Identify missing skills
    user_skills_lower = [skill.lower() for skill in user_skills]
    missing_skills = {}
    
    for skill, demand in skill_demand.items():
        if skill.lower() not in user_skills_lower:
            missing_skills[skill] = demand
    
    # Sort by demand
    missing_skills = dict(sorted(missing_skills.items(), key=lambda item: item[1], reverse=True))
    
    # Get top 10 missing skills
    top_missing = dict(list(missing_skills.items())[:10])
    
    # Calculate skill gap score
    gap_score = sum(missing_skills.values()) / len(missing_skills) if missing_skills else 0
    
    return {
        'skill_demand': skill_demand,
        'missing_skills': missing_skills,
        'top_missing_skills': top_missing,
        'gap_score': gap_score,
        'total_jobs_analyzed': total_jobs
    }

def get_free_learning_resources(skill, platforms):
    """Search free learning platforms for resources"""
    resources = []
    
    for platform, url_template in platforms.items():
        try:
            search_url = url_template.format(quote(skill))
            resources.append({
                'platform': platform,
                'url': search_url,
                'description': f"Free {skill} resources on {platform}"
            })
        except:
            pass
    
    # Add generic resource suggestions
    resources.extend([
        {
            'platform': 'GitHub',
            'url': f'https://github.com/search?q={quote(skill)}',
            'description': f"Open-source projects for {skill}"
        },
        {
            'platform': 'Google',
            'url': f'https://www.google.com/search?q=learn+{quote(skill)}+free',
            'description': f"Search for free {skill} resources"
        },
        {
            'platform': 'Towards Data Science',
            'url': f'https://towardsdatascience.com/search?q={quote(skill)}',
            'description': f"Articles about {skill}"
        }
    ])
    
    return resources

def generate_learning_recommendations(missing_skills, platforms):
    """Generate personalized learning recommendations"""
    recommendations = []
    
    for skill, demand in missing_skills.items():
        resources = get_free_learning_resources(skill, platforms)
        
        # Create project ideas
        project_ideas = [
            f"Build a small {skill} application",
            f"Create a tutorial explaining {skill} concepts",
            f"Solve 3 real-world problems using {skill}",
            f"Contribute to an open-source project using {skill}",
            f"Develop a prototype demonstrating {skill}",
            f"Write a blog post about applying {skill}"
        ]
        
        recommendations.append({
            'skill': skill,
            'demand': f"{demand:.1f}% of jobs",
            'resources': resources,
            'projects': project_ideas
        })
    
    return recommendations

def generate_report(config, gap_analysis, recommendations):
    """Generate visual report of skill gap analysis"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = f"{REPORTS_DIR}/{timestamp}"
    os.makedirs(report_dir, exist_ok=True)
    
    # Generate visualizations
    plt.style.use('ggplot')
    plt.rcParams.update({'font.size': 12})
    
    # Top demanded skills
    skill_demand = gap_analysis['skill_demand']
    top_skills = dict(sorted(skill_demand.items(), key=lambda item: item[1], reverse=True)[:15])
    
    plt.figure(figsize=(12, 8))
    plt.barh(list(top_skills.keys()), list(top_skills.values()), color='#2c3e50')
    plt.title('Top 15 In-Demand Skills', fontsize=16)
    plt.xlabel('Percentage of Jobs Requiring Skill', fontsize=12)
    plt.tight_layout()
    plt.savefig(f"{report_dir}/top_skills.png", dpi=100)
    plt.close()
    
    # Missing skills
    if gap_analysis['missing_skills']:
        plt.figure(figsize=(12, 6))
        plt.barh(list(gap_analysis['top_missing_skills'].keys()), 
                 list(gap_analysis['top_missing_skills'].values()), color='#e74c3c')
        plt.title('Your Top Missing Skills', fontsize=16)
        plt.xlabel('Percentage of Jobs Requiring Skill', fontsize=12)
        plt.tight_layout()
        plt.savefig(f"{report_dir}/missing_skills.png", dpi=100)
        plt.close()
    else:
        # Create a placeholder image if no missing skills
        plt.figure(figsize=(6, 1))
        plt.text(0.5, 0.5, "No significant skill gaps found!", 
                 ha='center', va='center', fontsize=16, color='green')
        plt.axis('off')
        plt.savefig(f"{report_dir}/missing_skills.png", dpi=100)
        plt.close()
    
    # Generate HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Skill Gap Analysis Report</title>
        <style>
            :root {{
                --primary: #2c3e50;
                --secondary: #3498db;
                --accent: #e74c3c;
                --light: #ecf0f1;
                --dark: #34495e;
                --success: #27ae60;
            }}
            
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f8f9fa;
                padding: 0;
                margin: 0;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            
            header {{
                background: linear-gradient(135deg, var(--primary) 0%, #4a6491 100%);
                color: white;
                padding: 40px 20px;
                text-align: center;
                margin-bottom: 30px;
                border-radius: 0 0 10px 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            
            h1 {{
                font-size: 2.5rem;
                margin-bottom: 10px;
            }}
            
            .date {{
                font-size: 1.1rem;
                opacity: 0.8;
                margin-top: 5px;
            }}
            
            .summary {{
                background-color: white;
                border-radius: 10px;
                padding: 25px;
                margin-bottom: 30px;
                box-shadow: 0 2px 15px rgba(0,0,0,0.05);
            }}
            
            .stats {{
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin: 20px 0;
            }}
            
            .stat-card {{
                flex: 1;
                min-width: 200px;
                background: linear-gradient(to right, #f8f9fa, #e9ecef);
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                border-left: 4px solid var(--secondary);
            }}
            
            .stat-value {{
                font-size: 2.2rem;
                font-weight: bold;
                color: var(--primary);
                margin: 10px 0;
            }}
            
            .skill-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                gap: 25px;
                margin: 25px 0;
            }}
            
            .chart-card {{
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 15px rgba(0,0,0,0.05);
            }}
            
            .chart-card img {{
                width: 100%;
                border-radius: 8px;
            }}
            
            .recommendations {{
                margin: 30px 0;
            }}
            
            .skill-card {{
                background-color: white;
                border-radius: 10px;
                padding: 25px;
                margin-bottom: 25px;
                box-shadow: 0 2px 15px rgba(0,0,0,0.05);
                border-top: 3px solid var(--secondary);
            }}
            
            .skill-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                padding-bottom: 15px;
                border-bottom: 1px solid #eee;
            }}
            
            .skill-name {{
                font-size: 1.4rem;
                color: var(--primary);
                font-weight: bold;
            }}
            
            .demand {{
                background-color: var(--secondary);
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.9rem;
            }}
            
            .resource-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 15px;
                margin: 15px 0;
            }}
            
            .resource-card {{
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                border-left: 3px solid var(--secondary);
                transition: transform 0.3s;
            }}
            
            .resource-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }}
            
            .resource-card a {{
                color: var(--primary);
                text-decoration: none;
                font-weight: bold;
            }}
            
            .resource-card a:hover {{
                text-decoration: underline;
            }}
            
            .projects {{
                margin-top: 20px;
            }}
            
            .project-list {{
                list-style-type: none;
                margin: 15px 0;
            }}
            
            .project-list li {{
                padding: 10px 0;
                border-bottom: 1px dashed #eee;
                display: flex;
                align-items: flex-start;
            }}
            
            .project-list li:before {{
                content: "•";
                color: var(--secondary);
                font-weight: bold;
                display: inline-block;
                width: 1em;
                margin-right: 10px;
                font-size: 1.2rem;
            }}
            
            .user-skills {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin: 15px 0;
            }}
            
            .skill-pill {{
                background-color: var(--secondary);
                color: white;
                padding: 8px 18px;
                border-radius: 20px;
                font-size: 0.9rem;
            }}
            
            footer {{
                text-align: center;
                padding: 20px;
                color: #7f8c8d;
                font-size: 0.9rem;
                margin-top: 40px;
            }}
            
            @media (max-width: 768px) {{
                .skill-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .stats {{
                    flex-direction: column;
                }}
            }}
        </style>
    </head>
    <body>
        <header>
            <div class="container">
                <h1>Automated Skill Gap Analysis</h1>
                <p class="date">Generated on {datetime.now().strftime("%B %d, %Y at %H:%M")}</p>
            </div>
        </header>
        
        <div class="container">
            <section class="summary">
                <h2>Analysis Summary</h2>
                <p>This report compares your current skills against market demands for your target roles.</p>
                
                <div class="stats">
                    <div class="stat-card">
                        <h3>Jobs Analyzed</h3>
                        <div class="stat-value">{gap_analysis['total_jobs_analyzed']}</div>
                        <p>Recent job postings across {len(config['job_roles']} roles</p>
                    </div>
                    
                    <div class="stat-card">
                        <h3>Skill Gap Score</h3>
                        <div class="stat-value {'success' if gap_analysis['gap_score'] < 30 else 'accent'}">{gap_analysis['gap_score']:.1f}/100</div>
                        <p>Lower scores indicate better alignment</p>
                    </div>
                    
                    <div class="stat-card">
                        <h3>Your Skills</h3>
                        <div class="user-skills">
                            {"".join([f'<div class="skill-pill">{skill}</div>' for skill in config['user_skills']])}
                        </div>
                    </div>
                </div>
            </section>
            
            <section class="skill-grid">
                <div class="chart-card">
                    <h3>Top In-Demand Skills</h3>
                    <img src="top_skills.png" alt="Top Skills Chart">
                </div>
                
                <div class="chart-card">
                    <h3>Your Skill Gaps</h3>
                    <img src="missing_skills.png" alt="Missing Skills Chart">
                </div>
            </section>
            
            <section class="recommendations">
                <h2>Personalized Learning Recommendations</h2>
                <p>Based on your skill gaps, here are resources to help you improve:</p>
                
                {"".join([f"""
                <div class="skill-card">
                    <div class="skill-header">
                        <div class="skill-name">{rec['skill']}</div>
                        <div class="demand">{rec['demand']}</div>
                    </div>
                    
                    <h4>Recommended Learning Resources</h4>
                    <div class="resource-grid">
                        {"".join([f"""
                        <div class="resource-card">
                            <a href="{res['url']}" target="_blank">{res['platform']}</a>
                            <p>{res['description']}</p>
                        </div>
                        """ for res in rec['resources']])}
                    </div>
                    
                    <div class="projects">
                        <h4>Project Ideas to Practice</h4>
                        <ul class="project-list">
                            {"".join([f'<li>{project}</li>' for project in rec['projects']])}
                        </ul>
                    </div>
                </div>
                """ for rec in recommendations])}
            </section>
        </div>
        
        <footer>
            <div class="container">
                <p>This report was automatically generated by GitHub Actions • Updated weekly</p>
                <p>To update your skills profile, edit the <code>skill_config.json</code> file in your repository</p>
            </div>
        </footer>
    </body>
    </html>
    """
    
    with open(f"{report_dir}/report.html", 'w') as f:
        f.write(html_content)
    
    return report_dir

def main():
    print("Starting Skill Gap Analysis...")
    
    # Load configuration
    config = load_config()
    print(f"Loaded configuration for {len(config['user_skills'])} skills")
    
    # Step 1: Scrape job market data
    print(f"Scraping job market data for: {', '.join(config['job_roles'])}")
    job_market_data = scrape_linkedin_jobs(
        config['job_roles'], 
        config['location'], 
        config['max_pages']
    )
    print(f"Found {len(job_market_data)} relevant job postings")
    
    # Step 2: Analyze skill gap
    print("Analyzing skill gap...")
    gap_analysis = analyze_skill_gap(config['user_skills'], job_market_data)
    
    # Step 3: Generate recommendations
    print("Generating learning recommendations...")
    recommendations = generate_learning_recommendations(
        gap_analysis['top_missing_skills'],
        config['platforms']
    )
    
    # Step 4: Generate report
    print("Generating report...")
    report_dir = generate_report(config, gap_analysis, recommendations)
    
    print("\n" + "="*50)
    print(f"Analysis complete! Report saved to: {report_dir}/report.html")
    print("="*50)

if __name__ == "__main__":
    main()
