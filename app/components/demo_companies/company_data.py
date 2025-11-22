"""
Demo Company Data
Contains 5 funny fake companies with their profiles and demo customers
"""

from typing import Dict, List, Any, Optional

# 5 Funny Fake Companies with Complete Profiles and Demo Customers
DEMO_COMPANIES = {
    "coffeecorp": {
        "id": "coffeecorp",
        "company_name": "CoffeeCorp Global",
        "core_business": "Caffeinating the world - because sleep is overrated and productivity is everything",
        "target_customers": ["Coffee Addicts", "Office Workers", "Insomniacs", "Productivity Seekers"],
        "industries_served": ["Coffee Manufacturing", "Office Services", "Sleep Deprivation", "Productivity Enhancement"],
        "products": "Premium Coffee Beans, Coffee Machines, Caffeine Pills, Coffee Insurance, Productivity Consulting",
        "value_propositions": "The finest coffee money can buy - guaranteed to keep you awake and productive",
        "location": "Coffee City, Caffeine State",
        "company_size": "Medium (51-200)",
        "location_type": "Coffee Roasting Facility",
        "business_intelligence": {
            "company_type": "Manufacturing & Service",
            "business_model": "B2B Coffee Sales & Services",
            "market_position": "Premium Coffee Leader",
            "growth_stage": "Mature",
            "revenue_model": "Coffee Sales & Subscription Services",
            "customer_segment": "Coffee Addicts & Productivity Seekers",
            "competitive_advantage": "Superior Coffee Quality & Caffeine Content",
            "key_metrics": "Cups per Day, Customer Caffeine Satisfaction, Productivity Increase",
            "challenges": "Coffee Bean Shortages, Caffeine Tolerance, Sleep Deprivation",
            "opportunities": "Coffee Innovation, International Coffee Markets, Caffeine Technology",
            "technology_adoption": "Advanced Coffee Roasting Technology",
            "regulatory_environment": "Coffee Quality Standards & Caffeine Regulations"
        },
        "demo_customers": [
            {
                "id": "corporate_coffee_chain",
                "company_name": "Corporate Coffee Chain",
                "industry": "Coffee Retail & Distribution",
                "size": "Large Enterprise",
                "location": "Global",
                "pain_points": ["Coffee Supply Chain", "Caffeine Quality Control", "Coffee ROI Tracking"],
                "goals": ["Complete Coffee Dominance", "Coffee Investment Returns", "Global Coffee Market Share"],
                "decision_process": "Coffee Committee Evaluation with CFO Approval",
                "value_drivers": ["Coffee Quality", "Caffeine Content", "Coffee Investment Value"],
                "website": "https://corporate-coffee-chain.com",
                "description": "A massive corporation that treats coffee as serious business fuel"
            },
            {
                "id": "local_coffee_shop",
                "company_name": "Local Coffee Shop",
                "industry": "Small Business Coffee Retail",
                "size": "Small Business",
                "location": "Local",
                "pain_points": ["Limited Coffee Budget", "Coffee Storage Space", "Coffee Knowledge Gap"],
                "goals": ["Essential Coffee Only", "Coffee Cost Control", "Coffee Education"],
                "decision_process": "Owner/Manager Quick Decision",
                "value_drivers": ["Coffee Affordability", "Coffee Simplicity", "Coffee Support"],
                "website": "https://local-coffee-shop.com",
                "description": "A small business that needs coffee but isn't sure why everyone's so addicted"
            },
            {
                "id": "caffeine_anonymous",
                "company_name": "Caffeine Anonymous",
                "industry": "Support Groups",
                "size": "Non-Profit",
                "location": "Community Centers",
                "pain_points": ["Coffee Addiction", "Caffeine Withdrawal", "Coffee Support"],
                "goals": ["Coffee Recovery", "Coffee Moderation", "Coffee Support"],
                "decision_process": "Group Consensus with Sponsor Approval",
                "value_drivers": ["Coffee Quality", "Coffee Support", "Coffee Community"],
                "website": "https://caffeine-anonymous.org",
                "description": "A support group for people with coffee addiction issues"
            }
        ]
    },
    
    "cloudyskies": {
        "id": "cloudyskies",
        "company_name": "CloudySkies Weather Solutions",
        "core_business": "Selling weather to people who already have it - because you can never have too much weather",
        "target_customers": ["Weather Enthusiasts", "Sunny Day Seekers", "Rain Lovers"],
        "industries_served": ["Weather Services", "Tourism", "Agriculture"],
        "products": "Premium Weather, Weather Subscriptions, Weather Insurance, Weather Consulting",
        "value_propositions": "The best weather money can buy - guaranteed to be weathery",
        "location": "Weather City, Cloud State",
        "company_size": "Small (1-50)",
        "location_type": "Weather Station",
        "business_intelligence": {
            "company_type": "Service",
            "business_model": "Weather as a Service",
            "market_position": "Premium Weather Provider",
            "growth_stage": "Startup",
            "revenue_model": "Weather Subscriptions",
            "customer_segment": "Weather Enthusiasts",
            "competitive_advantage": "Superior Weather Quality",
            "key_metrics": "Weather Satisfaction, Customer Weather Happiness",
            "challenges": "Weather Predictability, Weather Storage",
            "opportunities": "Weather Innovation, International Weather Markets",
            "technology_adoption": "Advanced Weather Technology",
            "regulatory_environment": "Weather Quality Standards"
        },
        "demo_customers": [
            {
                "id": "sunnyside_resort",
                "company_name": "SunnySide Resort",
                "industry": "Tourism & Hospitality",
                "size": "Medium Business",
                "location": "Tropical Paradise",
                "pain_points": ["Unpredictable Weather", "Weather Dependence", "Weather Complaints"],
                "goals": ["Perfect Weather Control", "Weather Predictability", "Weather Satisfaction"],
                "decision_process": "Resort Manager with Weather Committee",
                "value_drivers": ["Weather Quality", "Weather Reliability", "Weather Control"],
                "website": "https://sunnyside-resort.com",
                "description": "A resort that needs perfect weather for their guests"
            },
            {
                "id": "grumpy_farmers",
                "company_name": "Grumpy Farmers Co-op",
                "industry": "Agriculture",
                "size": "Cooperative",
                "location": "Rural Farmland",
                "pain_points": ["Weather Dependence", "Weather Unpredictability", "Weather Stress"],
                "goals": ["Weather Control", "Weather Predictability", "Weather Success"],
                "decision_process": "Farmer Committee with Weather Expert",
                "value_drivers": ["Weather Quality", "Weather Reliability", "Weather Support"],
                "website": "https://grumpy-farmers.coop",
                "description": "A group of farmers who are tired of weather being unpredictable"
            },
            {
                "id": "weather_channel_wannabes",
                "company_name": "Weather Channel Wannabes",
                "industry": "Media & Broadcasting",
                "size": "Small Business",
                "location": "TV Studio",
                "pain_points": ["Weather Accuracy", "Weather Credibility", "Weather Competition"],
                "goals": ["Weather Accuracy", "Weather Credibility", "Weather Success"],
                "decision_process": "Producer with Weather Expert",
                "value_drivers": ["Weather Quality", "Weather Accuracy", "Weather Credibility"],
                "website": "https://weather-wannabes.tv",
                "description": "Aspiring meteorologists who want to be the next Weather Channel"
            }
        ]
    },
    
    "artcorp": {
        "id": "artcorp",
        "company_name": "ArtCorp Studios",
        "core_business": "Creating art that nobody understands - because abstract is the new concrete",
        "target_customers": ["Art Collectors", "Museums", "Confused Art Lovers", "Art Critics", "Abstract Enthusiasts"],
        "industries_served": ["Art Manufacturing", "Museum Services", "Art Therapy", "Abstract Consulting", "Cultural Services"],
        "products": "Abstract Paintings, Sculptures, Art Insurance, Art Therapy, Confusion Services, Art Education",
        "value_propositions": "The most confusing and thought-provoking art available - guaranteed to make you question everything",
        "location": "Art District, Creative City",
        "company_size": "Medium (51-200)",
        "location_type": "Art Studio Complex",
        "business_intelligence": {
            "company_type": "Creative & Manufacturing",
            "business_model": "B2B Art Sales & Services",
            "market_position": "Leading Abstract Art Provider",
            "growth_stage": "Mature",
            "revenue_model": "Art Sales & Art Therapy Services",
            "customer_segment": "Art Collectors & Cultural Institutions",
            "competitive_advantage": "Superior Abstract Quality & Artistic Innovation",
            "key_metrics": "Art Pieces per Month, Customer Confusion Satisfaction, Museum Acquisitions",
            "challenges": "Art Interpretation, Abstract Understanding, Cultural Acceptance",
            "opportunities": "Art Innovation, International Art Markets, Digital Art Technology",
            "technology_adoption": "Advanced Art Creation Technology",
            "regulatory_environment": "Art Quality Standards & Cultural Regulations"
        },
        "demo_customers": [
            {
                "id": "modern_art_museum",
                "company_name": "Modern Art Museum",
                "industry": "Cultural Institution",
                "size": "Large Enterprise",
                "location": "Cultural District",
                "pain_points": ["Art Acquisition", "Exhibition Planning", "Visitor Engagement"],
                "goals": ["Cutting-Edge Art Collection", "Museum Innovation", "Cultural Impact"],
                "decision_process": "Curator Committee with Board Approval",
                "value_drivers": ["Art Quality", "Cultural Significance", "Museum Support"],
                "website": "https://modern-art-museum.org",
                "description": "A prestigious museum that needs cutting-edge abstract art for their collection"
            },
            {
                "id": "local_art_gallery",
                "company_name": "Local Art Gallery",
                "industry": "Small Business Art Retail",
                "size": "Small Business",
                "location": "Arts Quarter",
                "pain_points": ["Limited Art Budget", "Gallery Space", "Art Knowledge Gap"],
                "goals": ["Essential Art Only", "Gallery Cost Control", "Art Education"],
                "decision_process": "Gallery Owner Quick Decision",
                "value_drivers": ["Art Affordability", "Art Simplicity", "Gallery Support"],
                "website": "https://local-art-gallery.com",
                "description": "A small gallery that needs affordable art pieces but isn't sure what abstract means"
            },
            {
                "id": "art_therapy_center",
                "company_name": "Art Therapy Center",
                "industry": "Mental Health Services",
                "size": "Non-Profit",
                "location": "Community Center",
                "pain_points": ["Art Therapy Materials", "Patient Engagement", "Art Funding"],
                "goals": ["Art Therapy Success", "Patient Recovery", "Art Healing"],
                "decision_process": "Therapist Committee with Medical Approval",
                "value_drivers": ["Art Quality", "Therapeutic Value", "Art Support"],
                "website": "https://art-therapy-center.org",
                "description": "A mental health center that needs therapeutic art supplies for patient recovery"
            }
        ]
    },
    
    "invisibleink": {
        "id": "invisibleink",
        "company_name": "InvisibleInk Inc",
        "core_business": "Premium invisible writing solutions - because sometimes you need to write things that nobody can see",
        "target_customers": ["Secret Agents", "Magic Show Performers", "Spy Kids"],
        "industries_served": ["Espionage", "Entertainment", "Education"],
        "products": "Invisible Ink, Secret Writing Tools, Covert Communication, Spy Training",
        "value_propositions": "The most invisible ink available - guaranteed to be invisible",
        "location": "Secret Location, Hidden State",
        "company_size": "Small (1-50)",
        "location_type": "Secret Laboratory",
        "business_intelligence": {
            "company_type": "Technology",
            "business_model": "B2B Secret Services",
            "market_position": "Leading Invisible Ink Provider",
            "growth_stage": "Mature",
            "revenue_model": "Secret Service Sales",
            "customer_segment": "Secret Agents & Spies",
            "competitive_advantage": "Superior Invisibility Technology",
            "key_metrics": "Invisibility Success, Secret Communication Quality",
            "challenges": "Invisibility Maintenance, Secret Communication",
            "opportunities": "Invisibility Innovation, International Secret Markets",
            "technology_adoption": "Advanced Invisibility Technology",
            "regulatory_environment": "Secret Service Standards"
        },
        "demo_customers": [
            {
                "id": "secret_agent_supplies",
                "company_name": "Secret Agent Supplies",
                "industry": "Espionage Services",
                "size": "Medium Business",
                "location": "Undisclosed Location",
                "pain_points": ["Covert Communication", "Secret Writing", "Invisibility Issues"],
                "goals": ["Secret Communication", "Invisibility Success", "Secret Operations"],
                "decision_process": "Agent Committee with Security Clearance",
                "value_drivers": ["Invisibility Quality", "Secret Communication", "Security"],
                "website": "https://secret-agent-supplies.com",
                "description": "A supply company for professional secret agents and spies"
            },
            {
                "id": "magic_show_productions",
                "company_name": "Magic Show Productions",
                "industry": "Entertainment",
                "size": "Small Business",
                "location": "Theater District",
                "pain_points": ["Magic Tricks", "Audience Engagement", "Illusion Success"],
                "goals": ["Magic Success", "Audience Amazement", "Illusion Quality"],
                "decision_process": "Magician with Magic Committee",
                "value_drivers": ["Invisibility Quality", "Magic Success", "Audience Engagement"],
                "website": "https://magic-show-productions.com",
                "description": "A production company that creates magic shows and illusions"
            },
            {
                "id": "spy_kids_academy",
                "company_name": "Spy Kids Academy",
                "industry": "Education",
                "size": "Educational Institution",
                "location": "Secret Training Facility",
                "pain_points": ["Spy Training", "Secret Education", "Covert Skills"],
                "goals": ["Spy Education", "Secret Skills", "Covert Training"],
                "decision_process": "Academy Director with Security Committee",
                "value_drivers": ["Invisibility Quality", "Secret Education", "Spy Training"],
                "website": "https://spy-kids-academy.edu",
                "description": "An academy that trains future secret agents and spies"
            }
        ]
    },
    
    "timetravel": {
        "id": "timetravel",
        "company_name": "TimeTravel Logistics",
        "core_business": "Shipping packages to yesterday - because sometimes you need to deliver things before they're sent",
        "target_customers": ["Time Travelers", "Historical Societies", "Paradox Prevention"],
        "industries_served": ["Logistics", "Time Travel", "Historical Services"],
        "products": "Time Shipping, Historical Delivery, Paradox Prevention, Time Insurance",
        "value_propositions": "The most reliable time travel logistics available",
        "location": "Time Space, Temporal State",
        "company_size": "Medium (51-200)",
        "location_type": "Time Travel Hub",
        "business_intelligence": {
            "company_type": "Logistics",
            "business_model": "B2B Time Travel Services",
            "market_position": "Leading Time Travel Logistics",
            "growth_stage": "Mature",
            "revenue_model": "Time Travel Service Sales",
            "customer_segment": "Time Travelers & Historians",
            "competitive_advantage": "Superior Time Travel Technology",
            "key_metrics": "Time Travel Success, Delivery Accuracy",
            "challenges": "Time Travel Complexity, Paradox Prevention",
            "opportunities": "Time Travel Innovation, Historical Markets",
            "technology_adoption": "Advanced Time Travel Technology",
            "regulatory_environment": "Time Travel Safety Standards"
        },
        "demo_customers": [
            {
                "id": "yesterdays_news",
                "company_name": "Yesterday's News Corp",
                "industry": "Media & Broadcasting",
                "size": "Large Enterprise",
                "location": "Time Media Hub",
                "pain_points": ["News Timing", "Historical Accuracy", "Time Travel Logistics"],
                "goals": ["News Accuracy", "Historical Reporting", "Time Travel Success"],
                "decision_process": "News Director with Time Committee",
                "value_drivers": ["Time Travel Quality", "News Accuracy", "Historical Reporting"],
                "website": "https://yesterdays-news.com",
                "description": "A news corporation that delivers news before it happens"
            },
            {
                "id": "historical_society",
                "company_name": "Historical Society",
                "industry": "Historical Services",
                "size": "Non-Profit Organization",
                "location": "Historical Archive",
                "pain_points": ["Historical Accuracy", "Artifact Preservation", "Time Travel Logistics"],
                "goals": ["Historical Preservation", "Artifact Accuracy", "Time Travel Success"],
                "decision_process": "Society Board with Historical Committee",
                "value_drivers": ["Time Travel Quality", "Historical Accuracy", "Artifact Preservation"],
                "website": "https://historical-society.org",
                "description": "A society dedicated to preserving and studying historical artifacts"
            },
            {
                "id": "paradox_prevention",
                "company_name": "Paradox Prevention Agency",
                "industry": "Time Travel Services",
                "size": "Government Agency",
                "location": "Time Travel Headquarters",
                "pain_points": ["Paradox Prevention", "Time Travel Safety", "Temporal Stability"],
                "goals": ["Paradox Prevention", "Time Travel Safety", "Temporal Stability"],
                "decision_process": "Agency Director with Time Committee",
                "value_drivers": ["Time Travel Quality", "Paradox Prevention", "Temporal Stability"],
                "website": "https://paradox-prevention.gov",
                "description": "A government agency that prevents time travel paradoxes and disasters"
            }
        ]
    }
}

def get_company_by_id(company_id: str) -> Optional[Dict[str, Any]]:
    """Get a demo company by its ID"""
    return DEMO_COMPANIES.get(company_id)

def get_customers_for_company(company_id: str) -> List[Dict[str, Any]]:
    """Get demo customers for a specific company"""
    company = get_company_by_id(company_id)
    if company:
        return company.get("demo_customers", [])
    return []

def get_all_company_ids() -> List[str]:
    """Get all available company IDs"""
    return list(DEMO_COMPANIES.keys())

def get_company_display_info() -> List[Dict[str, str]]:
    """Get company display information for dropdown"""
    return [
        {
            "id": company_id,
            "name": company_data["company_name"],
            "description": company_data["core_business"]
        }
        for company_id, company_data in DEMO_COMPANIES.items()
    ]
