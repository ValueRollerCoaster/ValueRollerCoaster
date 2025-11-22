from typing import Dict, Any, List

class DynamicExampleGenerator:
    """Generates examples based on actual company context"""
    
    def __init__(self):
        from app.utils.universal_company_context_extractor import UniversalCompanyContextExtractor
        self.context_extractor = UniversalCompanyContextExtractor()
    
    def generate_field_examples(self, field_name: str, main_category: str, subcategory: str) -> List[Dict[str, str]]:
        """Generate examples based on actual company context"""
        
        # Extract company context
        company_context = self.context_extractor.extract_field_specific_context(
            field_name, main_category, subcategory
        )
        
        # Generate examples based on actual company data
        examples = self._generate_company_specific_examples(field_name, main_category, subcategory, company_context)
        
        return examples
    
    def _generate_company_specific_examples(self, field_name: str, main_category: str, 
                                          subcategory: str, company_context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate examples specific to the company's actual context"""
        
        company_basics = company_context["company_basics"]
        industry_context = company_context["industry_context"]
        capability_context = company_context["capability_context"]
        value_context = company_context["value_context"]
        
        company_name = company_basics.get("name", "the company")
        core_business = company_basics.get("core_business", "the company's business")
        target_industries = industry_context.get("target_industries", [])
        core_capabilities = capability_context.get("core_capabilities", [])
        customer_outcomes = value_context.get("customer_outcomes", [])
        
        # Generate examples based on field type and company context
        if main_category == "Technical Value":
            return self._generate_technical_examples(field_name, subcategory, company_name, 
                                                   core_business, target_industries, core_capabilities)
        
        elif main_category == "Business Value":
            return self._generate_business_examples(field_name, subcategory, company_name, 
                                                  core_business, customer_outcomes, target_industries)
        
        elif main_category == "Strategic Value":
            return self._generate_strategic_examples(field_name, subcategory, company_name, 
                                                   core_business, target_industries)
        
        elif main_category == "After Sales Value":
            return self._generate_service_examples(field_name, subcategory, company_name, 
                                                 core_business, core_capabilities)
        
        else:
            return self._generate_generic_examples(field_name, company_name, core_business)
    
    def _generate_technical_examples(self, field_name: str, subcategory: str, company_name: str,
                                   core_business: str, target_industries: List[str], 
                                   core_capabilities: List[str]) -> List[Dict[str, str]]:
        """Generate technical value examples"""
        
        examples = []
        
        # Use actual company capabilities and industries
        capabilities_text = ', '.join(core_capabilities[:3]) if core_capabilities else "technical expertise"
        industries_text = ', '.join(target_industries[:2]) if target_industries else "target industries"
        
        if subcategory == "Quality":
            examples.append({
                "text": f"{company_name}'s {core_business.lower()} ensures consistent quality through {capabilities_text}.",
                "explanation": "Focuses on quality aspects using actual company capabilities"
            })
        
        elif subcategory == "Performance":
            examples.append({
                "text": f"{company_name} delivers superior performance in {industries_text} through advanced {core_business.lower()}.",
                "explanation": "Highlights performance benefits for actual target industries"
            })
        
        elif subcategory == "Innovation":
            examples.append({
                "text": f"{company_name} drives innovation in {core_business.lower()} through continuous {capabilities_text}.",
                "explanation": "Emphasizes innovation using actual company capabilities"
            })
        
        elif subcategory == "Sustainability":
            examples.append({
                "text": f"{company_name} promotes sustainability in {industries_text} through eco-friendly {core_business.lower()}.",
                "explanation": "Addresses environmental benefits for actual target industries"
            })
        
        return examples
    
    def _generate_business_examples(self, field_name: str, subcategory: str, company_name: str,
                                  core_business: str, customer_outcomes: List[str], 
                                  target_industries: List[str]) -> List[Dict[str, str]]:
        """Generate business value examples"""
        
        examples = []
        
        outcomes_text = ', '.join(customer_outcomes[:2]) if customer_outcomes else "business benefits"
        industries_text = ', '.join(target_industries[:2]) if target_industries else "target industries"
        
        if subcategory == "Cost Savings":
            examples.append({
                "text": f"{company_name} reduces operational costs in {industries_text} through efficient {core_business.lower()}.",
                "explanation": "Addresses cost savings for actual target industries"
            })
        
        elif subcategory == "Revenue Growth":
            examples.append({
                "text": f"{company_name} enables revenue growth through {outcomes_text} in {core_business.lower()}.",
                "explanation": "Focuses on revenue benefits using actual customer outcomes"
            })
        
        return examples
    
    def _generate_strategic_examples(self, field_name: str, subcategory: str, company_name: str,
                                   core_business: str, target_industries: List[str]) -> List[Dict[str, str]]:
        """Generate strategic value examples"""
        
        examples = []
        industries_text = ', '.join(target_industries[:2]) if target_industries else "target industries"
        
        if subcategory == "Competitive Advantage":
            examples.append({
                "text": f"{company_name} provides competitive advantage in {industries_text} through superior {core_business.lower()}.",
                "explanation": "Emphasizes competitive positioning in actual target industries"
            })
        
        elif subcategory == "Risk Mitigation":
            examples.append({
                "text": f"{company_name} reduces risks in {industries_text} through reliable {core_business.lower()}.",
                "explanation": "Addresses risk mitigation for actual target industries"
            })
        
        return examples
    
    def _generate_service_examples(self, field_name: str, subcategory: str, company_name: str,
                                 core_business: str, core_capabilities: List[str]) -> List[Dict[str, str]]:
        """Generate after-sales service examples"""
        
        examples = []
        capabilities_text = ', '.join([cap for cap in core_capabilities if 'service' in cap.lower() or 'support' in cap.lower()][:2]) if core_capabilities else "service capabilities"
        
        if subcategory == "Support":
            examples.append({
                "text": f"{company_name} provides comprehensive support for {core_business.lower()} through {capabilities_text}.",
                "explanation": "Highlights support capabilities using actual company services"
            })
        
        elif subcategory == "Training":
            examples.append({
                "text": f"{company_name} offers training and expertise for {core_business.lower()} to maximize customer value.",
                "explanation": "Emphasizes training and expertise development"
            })
        
        return examples
    
    def _generate_generic_examples(self, field_name: str, company_name: str, core_business: str) -> List[Dict[str, str]]:
        """Generate generic examples when specific category is not found"""
        
        return [{
            "text": f"{company_name} delivers value through {core_business.lower()}.",
            "explanation": "General example using company's core business"
        }]
