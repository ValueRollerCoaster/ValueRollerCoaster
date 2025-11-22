# Category and subcategory structure for value components
COMPONENT_STRUCTURES = {
    "Technical Value": {
        "icon": "🛠️",
        "description": "Technical aspects of your product or service",
        "subcategories": {
            "Quality": {
                "weight": 25, # Placeholder weight
                "items": [
                    {"name": "Certificates and Skills", "description": "Describe your team's certifications and unique skills.", "tooltip": "List your team's relevant certifications, licenses, and special skills that make you qualified to deliver this product or service.", "input_type": "text_area"},
                    {"name": "Compliance and Standards", "description": "Detail compliance with industry standards and regulations.", "tooltip": "Describe the industry standards and regulations your product meets, and how this ensures quality and trustworthiness.", "input_type": "text_area"},
                    {"name": "Testing and Validation", "description": "Explain your product's testing and validation processes.", "tooltip": "Describe how you test your product to ensure it works properly and meets quality standards.", "input_type": "text_area"}
                ]
            },
            "Performance": {
                "weight": 25, # Placeholder weight
                "items": [
                    {"name": "Speed and Efficiency", "description": "Highlight how your product enhances operational speed and efficiency.", "tooltip": "Describe how your product makes things faster and more efficient for customers.", "input_type": "text_area"},
                    {"name": "Reliability and Uptime", "description": "Describe product reliability and uptime guarantees.", "tooltip": "Explain how reliable your product is and what uptime guarantees you provide to customers.", "input_type": "text_area"},
                    {"name": "Scalability and Flexibility", "description": "Detail product scalability and flexibility to adapt to changing needs.", "tooltip": "Describe how your product can grow with the customer and adapt to their changing needs.", "input_type": "text_area"}
                ]
            },
            "Innovation": {
                "weight": 25, # Placeholder weight
                "items": [
                    {"name": "Unique Features", "description": "List any unique or patented features of your product.", "tooltip": "Describe what makes your product special and different from competitors.", "input_type": "text_area"},
                    {"name": "R&D Investment", "description": "Mention ongoing research and development efforts.", "tooltip": "Describe how your company invests in research and development to keep improving your product.", "input_type": "text_area"},
                    {"name": "Future-Proofing", "description": "Explain how your product is designed for future advancements.", "tooltip": "Describe how your product is built to stay relevant and useful as technology changes.", "input_type": "text_area"}
                ]
            },
            "Sustainability": {
                "weight": 25, # Placeholder weight
                "items": [
                    {"name": "Environmental Impact", "description": "Describe your product's positive environmental impact (e.g., energy saving, waste reduction).", "tooltip": "Explain how your product helps the environment, like saving energy or reducing waste.", "input_type": "text_area"},
                    {"name": "Ethical Sourcing", "description": "Detail ethical sourcing practices for materials and components.", "tooltip": "Describe how you ensure your materials and components come from ethical and responsible sources.", "input_type": "text_area"},
                    {"name": "Circular Economy Contribution", "description": "Explain how your product supports circular economy principles.", "tooltip": "Describe how your product can be reused, recycled, or repurposed to reduce waste.", "input_type": "text_area"}
                ]
            }
        }
    },
    "Business Value": {
        "icon": "💰",
        "description": "Financial and operational benefits for the customer",
        "subcategories": {
            "Cost Savings": {
                "weight": 30,
                "items": [
                    {"name": "Operational Cost Reduction", "description": "How does your product reduce daily operational expenses?", "tooltip": "Describe how your product helps customers save money on their daily operations.", "input_type": "text_area"},
                    {"name": "Maintenance Savings", "description": "Describe any reduction in maintenance costs.", "tooltip": "Explain how your product reduces maintenance costs and extends equipment life.", "input_type": "text_area"},
                    {"name": "Energy Efficiency Savings", "description": "Quantify energy savings due to your product.", "tooltip": "Describe how your product helps customers save energy and reduce energy costs.", "input_type": "text_area"}
                ]
            },
            "Revenue Growth": {
                "weight": 30,
                "items": [
                    {"name": "Increased Sales", "description": "How does your product help customers increase their sales or market share?", "tooltip": "Describe how your product helps customers sell more and grow their business.", "input_type": "text_area"},
                    {"name": "New Market Access", "description": "Does your product open up new markets for the customer?", "tooltip": "Explain how your product helps customers reach new markets or customer groups.", "input_type": "text_area"},
                    {"name": "Faster Time-to-Market", "description": "How does your product accelerate product launch timelines?", "tooltip": "Describe how your product helps customers launch their products faster.", "input_type": "text_area"}
                ]
            },
            "Efficiency Gains": {
                "weight": 40,
                "items": [
                    {"name": "Process Optimization", "description": "How does your product streamline customer processes?", "tooltip": "Describe how your product makes customer processes faster and more efficient.", "input_type": "text_area"},
                    {"name": "Resource Utilization", "description": "Describe improved utilization of customer resources (e.g., labor, equipment).", "tooltip": "Explain how your product helps customers get more value from their existing resources.", "input_type": "text_area"},
                    {"name": "Automation Benefits", "description": "What are the benefits of automation provided by your product?", "tooltip": "Describe how your product automates tasks to save time and reduce errors.", "input_type": "text_area"}
                ]
            }
        }
    },
    "Strategic Value": {
        "icon": "🎯",
        "description": "Long-term competitive advantages and market positioning",
        "subcategories": {
            "Competitive Advantage": {
                "weight": 50,
                "items": [
                    {"name": "Market Differentiation", "description": "How does your product help customers differentiate themselves from competitors?", "tooltip": "Explain how your product helps customers stand out from their competitors.", "input_type": "text_area"},
                    {"name": "Brand Reputation Enhancement", "description": "How does using your product improve the customer's brand image?", "tooltip": "Describe how your product helps improve the customer's reputation and credibility.", "input_type": "text_area"}
                ]
            },
            "Risk Mitigation": {
                "weight": 50,
                "items": [
                    {"name": "Security and Compliance", "description": "How does your product help mitigate security risks or ensure compliance?", "tooltip": "Describe how your product helps customers stay secure and meet regulatory requirements.", "input_type": "text_area"},
                    {"name": "Business Continuity", "description": "Describe how your product enhances business continuity during disruptions.", "tooltip": "Explain how your product helps customers keep their business running during problems or disruptions.", "input_type": "text_area"}
                ]
            },
            "Partnership Development": {
                "weight": 40,
                "items": [
                    {"name": "Co-Creation Opportunities", "description": "Describe opportunities for joint development or custom solutions tailored to the customer.", "tooltip": "Describe how you work with customers to create custom solutions that meet their specific needs.", "input_type": "text_area"},
                    {"name": "Strategic Roadmap Alignment", "description": "How does your product and company roadmap align with the customer's long-term goals?", "tooltip": "Explain how your product's future development aligns with the customer's long-term business goals.", "input_type": "text_area"},
                    {"name": "Relationship Management", "description": "Explain how your organization supports strategic relationships, e.g. key account management, regular reviews.", "tooltip": "Describe how your organization provides dedicated support and relationship management for important customers.", "input_type": "text_area"}
                ]
            }
        }
    },
    "After Sales Value": {
        "icon": "🤝",
        "description": "Support and service benefits after purchase",
        "subcategories": {
            "Customer Support": {
                "weight": 50,
                "items": [
                    {"name": "Availability and Responsiveness", "description": "Detail the availability and responsiveness of your support team.", "tooltip": "Describe when and how quickly your support team is available to help customers.", "input_type": "text_area"},
                    {"name": "Training and Onboarding", "description": "Describe training and onboarding resources provided.", "tooltip": "Describe the training and support you provide to help customers learn how to use your product.", "input_type": "text_area"},
                ]
            },
            "Maintenance and Updates": {
                "weight": 50,
                "items": [
                    {"name": "Regular Updates", "description": "Explain the frequency and scope of product updates.", "tooltip": "Describe how often you update your product and what improvements customers can expect.", "input_type": "text_area"},
                    {"name": "Proactive Maintenance", "description": "Describe proactive maintenance programs to prevent issues.", "tooltip": "Explain how you proactively maintain your product to prevent problems before they happen.", "input_type": "text_area"}
                ]
            },
            "User Experience & Integration": {
                "weight": 30,
                "items": [
                    {"name": "Ease of Use", "description": "Describe how your product is intuitive and user-friendly for the end user.", "tooltip": "Explain how your product is designed to be easy to learn and use.", "input_type": "text_area"},
                    {"name": "Integration Simplicity", "description": "Explain how easily your product integrates into existing workflows or systems.", "tooltip": "Describe how easy it is to integrate your product with existing systems and workflows.", "input_type": "text_area"},
                    {"name": "User Adoption & Feedback", "description": "Provide evidence or examples of high adoption rates or positive end-user feedback.", "tooltip": "Share examples of how well users adopt your product and what positive feedback you've received.", "input_type": "text_area"}
                ]
            }
        }
    }
} 

# st.write("COMPONENT_STRUCTURES:", COMPONENT_STRUCTURES) 