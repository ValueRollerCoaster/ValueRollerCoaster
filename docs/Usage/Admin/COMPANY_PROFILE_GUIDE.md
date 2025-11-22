# Company Profile: Complete Guide

<div align="center">

# 🏢

**Everything you need to know about Company Profile configuration**

</div>

---

## 📋 Table of Contents

- [What is Company Profile?](#what-is-company-profile)
- [Why It Matters](#why-it-matters)
- [Complete Field Reference](#complete-field-reference)
- [How It Affects the Application](#how-it-affects-the-application)
- [Step-by-Step Configuration](#step-by-step-configuration)
- [Editing Your Profile](#editing-your-profile)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## What is Company Profile?

The **Company Profile** is the foundation of your Value Rollercoaster setup. It's a comprehensive configuration that customizes the entire application for your specific business.

### Core Purpose

The Company Profile:
- **Customizes AI Analysis**: All AI prompts adapt to your company's business
- **Defines Your Market**: Focuses analysis on your customers and industries
- **Enables Value Components**: Provides context for value component generation
- **Generates Industry Frameworks**: Creates industry-specific frameworks automatically
- **Brands the Application**: Applies your company colors and logo throughout

### One-Time Setup

The Company Profile is configured **once** during initial setup, but can be **edited anytime** via the admin interface. Changes take effect immediately and affect all future AI analysis.

---

## Why It Matters

### Impact on AI Analysis

Every AI-powered feature in Value Rollercoaster uses your Company Profile:

1. **Persona Generation**: AI analyzes prospects in the context of your business
2. **Value Alignment**: Matches your values with prospect needs based on your profile
3. **Market Intelligence**: Provides industry insights relevant to your business
4. **Value Components**: AI suggests value components based on your profile

### Impact on User Experience

- **Relevant Insights**: All analysis focuses on your target market
- **Custom Value Components**: Value propositions match your offerings
- **Professional Branding**: Company name and colors throughout the app
- **Industry Frameworks**: Frameworks generated for your specific industries

### Without Company Profile

- Generic AI analysis that doesn't understand your business
- No industry-specific frameworks
- Limited value component suggestions
- No branding customization

---

## Complete Field Reference

### 📋 Company Information

#### Company Name *
- **Type**: Text input
- **Required**: Yes
- **Purpose**: Your company's official name
- **Used In**: All AI prompts, branding, persona generation
- **Example**: "Acme Manufacturing Corp"

#### Company Size
- **Type**: Dropdown select
- **Required**: No
- **Options**: Startup, Small (1-50), Medium (51-200), Large (201-1000), Enterprise (1000+)
- **Purpose**: Helps AI understand your company scale
- **Used In**: Market intelligence, competitive analysis

#### Location Type *
- **Type**: Dropdown select
- **Required**: Yes
- **Options**: Single Location, Multiple Locations, Remote-First, Global Operations, Regional Focus, Local Market
- **Purpose**: Geographic organization of your company
- **Used In**: Market analysis, persona generation

#### Primary Location
- **Type**: Text input
- **Required**: No
- **Purpose**: Main office, headquarters, or primary base
- **Used In**: Market intelligence, location-based analysis
- **Example**: "Berlin, Germany"

#### Core Business Description *
- **Type**: Text area (2-3 sentences)
- **Required**: Yes
- **Purpose**: What your company does
- **Used In**: All AI prompts, value component generation, persona generation
- **Best Practice**: Be specific, not generic
- **Example**: "We manufacture high-performance hydraulic systems for heavy machinery in the mining and construction industries."

---

### 🎯 Target Market

#### Target Customers *
- **Type**: Multi-select dropdown
- **Required**: Yes (at least one)
- **Standard Options**: OEMs, Distributors, End Users, System Integrators, Resellers, Consultants, Other
- **Custom Options**: Can add custom customer types with AI validation
- **Purpose**: Who your primary customers are
- **Used In**: Persona generation, value alignment, market intelligence
- **AI Enhancement**: AI can suggest customer types based on your business

#### Industries Served *
- **Type**: Multi-select dropdown
- **Required**: Yes (at least one)
- **Standard Options**: Mining, Construction, Agriculture, Manufacturing, Automotive, Aerospace, Marine, Oil & Gas, Utilities, Other
- **Custom Options**: Can add custom industries with AI validation
- **Purpose**: Which industries you serve
- **Used In**: Industry framework generation, market intelligence, persona generation
- **AI Enhancement**: AI can suggest industries based on your business

#### AI-Powered Suggestions
- **AI Suggest**: Get AI suggestions for customer types or industries
- **Validate & Add**: AI validates custom entries before adding
- **Duplicate Detection**: Prevents adding similar options

---

### 🛠️ Products & Services

#### Products and Services *
- **Type**: Text area
- **Required**: Yes
- **Purpose**: Describe your main products and services
- **Used In**: Value component generation, persona generation, value alignment
- **Best Practice**: Be specific, list key offerings
- **Example**: "Hydraulic pumps, valves, cylinders, and complete hydraulic systems for heavy machinery"

#### Key Value Propositions
- **Type**: Text area
- **Required**: No (but recommended)
- **Purpose**: What makes your products/services unique
- **Used In**: Value component generation, value alignment, persona generation
- **Best Practice**: Focus on customer benefits, not just features
- **Example**: "Industry-leading reliability with 99.9% uptime guarantee and 24/7 technical support"

---

### 🧠 Business Intelligence

This section helps AI models understand your company's business model and market position.

#### Company Type *
- **Type**: Dropdown select
- **Required**: Yes
- **Options**: Manufacturer & Technology Owner, Service Provider, Technology Company, Consulting, Platform Provider, Distributor, Other
- **Purpose**: Primary business classification
- **Used In**: Market intelligence, competitive analysis

#### Business Model *
- **Type**: Dropdown select
- **Required**: Yes
- **Options**: B2B OEM Supplier, B2B, B2C, SaaS, Consulting, Platform, Marketplace, Subscription, Other
- **Purpose**: How you generate revenue
- **Used In**: Market intelligence, value alignment

#### Value Delivery Method *
- **Type**: Dropdown select
- **Required**: Yes
- **Options**: Product, Service, Platform, Solution, Consultation, Other
- **Purpose**: How you deliver value to customers
- **Used In**: Value component generation, value alignment

#### Market Position *
- **Type**: Dropdown select
- **Required**: Yes
- **Options**: Leader, Challenger, Specialist, Niche, Emerging, Other
- **Purpose**: Your position in the market
- **Used In**: Competitive analysis, market intelligence

#### Company Size (BI)
- **Type**: Dropdown select
- **Required**: Yes
- **Options**: Startup, Small, Medium, Large, Enterprise
- **Purpose**: Company size for business intelligence
- **Used In**: Market intelligence, competitive analysis

#### Maturity Stage *
- **Type**: Dropdown select
- **Required**: Yes
- **Options**: Startup, Growth, Mature, Established, Legacy
- **Purpose**: Company lifecycle stage
- **Used In**: Market intelligence, strategic recommendations

#### Geographic Scope *
- **Type**: Dropdown select
- **Required**: Yes
- **Options**: Local, Regional, National, International, Global
- **Purpose**: Geographic market coverage
- **Used In**: Market intelligence, persona generation

#### Industry Focus *
- **Type**: Dropdown select
- **Required**: Yes
- **Options**: Single Industry, Multi-Industry, Industry Agnostic
- **Purpose**: Industry specialization level
- **Used In**: Industry framework generation

#### Revenue Model *
- **Type**: Dropdown select
- **Required**: Yes
- **Options**: One-time Sales, Recurring Revenue, Subscription, Usage-based, Hybrid
- **Purpose**: Revenue generation model
- **Used In**: Market intelligence, value alignment

#### Customer Relationship Type *
- **Type**: Dropdown select
- **Required**: Yes
- **Options**: Transactional, Relationship-based, Partnership, Platform-based
- **Purpose**: Type of customer relationships
- **Used In**: Value alignment, persona generation

#### Innovation Focus *
- **Type**: Dropdown select
- **Required**: Yes
- **Options**: Product Innovation, Process Innovation, Business Model Innovation, Technology Innovation, Customer Experience Innovation
- **Purpose**: Primary innovation area
- **Used In**: Market intelligence, competitive analysis

#### Competitive Advantage Type *
- **Type**: Dropdown select
- **Required**: Yes
- **Options**: Technology, Cost, Quality, Service, Brand, Network Effects, Other
- **Purpose**: Primary competitive advantage
- **Used In**: Value component generation, value alignment

---

### 🎨 Branding

#### Primary Color
- **Type**: Color picker
- **Required**: No
- **Purpose**: Primary brand color
- **Used In**: Application theming, branding
- **Format**: Hex color code (e.g., #FF5733)

#### Logo URL
- **Type**: Text input (URL)
- **Required**: No
- **Purpose**: Company logo image URL
- **Used In**: Application branding
- **Format**: Full URL to image (e.g., https://example.com/logo.png)
- **Note**: Image should be publicly accessible

---

## How It Affects the Application

### 1. AI Prompt Customization

**All AI prompts** include your Company Profile context:

```
Company: [Your Company Name]
Core Business: [Your Core Business]
Target Customers: [Your Target Customers]
Industries Served: [Your Industries]
Products/Services: [Your Products]
```

This ensures AI analysis is **relevant to your business**.

### 2. Industry Framework Generation

**Industry Frameworks** are automatically generated for each industry in your "Industries Served" list:

- **NACE Codes**: Industry classification codes
- **Key Metrics**: Industry-specific metrics
- **Trend Areas**: Current industry trends
- **Value Drivers**: What drives value in your industries
- **Pain Points**: Common industry challenges
- **Technology Focus**: Technology trends in your industries

### 3. Value Component Generation

When generating value components, AI uses:
- **Products & Services**: To suggest relevant value components
- **Value Propositions**: To align components with your messaging
- **Target Customers**: To focus on customer benefits
- **Business Model**: To understand value delivery

### 4. Persona Generation

During persona generation, AI considers:
- **Your Industries**: Analyzes prospects in context of your industries
- **Your Customers**: Focuses on customer types you serve
- **Your Business Model**: Understands how you operate
- **Your Market Position**: Provides competitive context

### 5. Value Alignment

Value alignment uses:
- **Your Value Components**: Matches with prospect needs
- **Your Industries**: Industry-specific alignment
- **Your Business Model**: Understands value delivery
- **Your Competitive Advantage**: Highlights differentiation

---

## Step-by-Step Configuration

### Initial Setup

1. **Access Company Profile**
   - Login as admin (`default_user`)
   - Go to **🔧 Admin Tools** → **🏢 Company Profile**
   - Click **✏️ Edit Company Profile**

2. **Fill Company Information**
   - Enter company name (required)
   - Select company size
   - Choose location type (required)
   - Enter primary location
   - Write core business description (required, 2-3 sentences)

3. **Configure Target Market**
   - Select target customers (required, at least one)
   - Select industries served (required, at least one)
   - Use AI suggestions if needed
   - Add custom options with AI validation

4. **Describe Products & Services**
   - Enter products and services (required)
   - Enter value propositions (recommended)

5. **Set Business Intelligence**
   - Select all business intelligence fields (all required)
   - Be accurate - this affects AI analysis quality

6. **Configure Branding** (Optional)
   - Choose primary color
   - Enter logo URL

7. **Save Profile**
   - Click **Save Company Profile**
   - Verify success message
   - Profile is now active

### Editing Existing Profile

1. **Access Edit Mode**
   - Go to **🔧 Admin Tools** → **🏢 Company Profile**
   - Click **✏️ Edit Company Profile**

2. **Make Changes**
   - All fields are pre-filled with current values
   - Modify any fields as needed
   - Changes take effect immediately

3. **Save Changes**
   - Click **Save Company Profile**
   - Changes are applied immediately

---

## Editing Your Profile

### When to Edit

- **Business Changes**: Company pivots, new products, market expansion
- **Industry Changes**: Entering new industries, exiting industries
- **Customer Changes**: New customer segments, changed focus
- **Branding Updates**: Logo changes, color updates

### How Changes Affect the App

- **Immediate Effect**: Changes apply to all new AI analysis
- **Existing Data**: Previous personas and analyses are not changed
- **Framework Regeneration**: Industry frameworks regenerate automatically
- **Value Components**: May need to regenerate value components

### Best Practices for Editing

- **Review Before Saving**: Double-check all changes
- **Test After Changes**: Generate a test persona to verify changes
- **Update Value Components**: Consider regenerating value components
- **Refresh Frameworks**: Refresh AI frameworks after major changes

---

## Best Practices

### Company Information

- **Be Specific**: "We manufacture hydraulic systems" not "We make things"
- **Accurate Descriptions**: Use real, accurate information
- **Complete Information**: Fill out all required fields
- **Regular Updates**: Update when business changes

### Target Market

- **Select All Relevant**: Include all industries you serve
- **Use AI Suggestions**: Let AI suggest relevant options
- **Validate Custom Entries**: Use AI validation for custom entries
- **Avoid Duplicates**: Check for similar options before adding

### Products & Services

- **Be Comprehensive**: List all major products/services
- **Focus on Value**: Emphasize customer benefits
- **Keep Updated**: Update when offerings change
- **Be Specific**: Avoid generic descriptions

### Business Intelligence

- **Be Honest**: Accurate information improves AI analysis
- **Complete All Fields**: All fields are used in analysis
- **Review Periodically**: Update as business evolves
- **Match Reality**: Ensure selections match actual business

### Branding

- **Professional Colors**: Use brand-appropriate colors
- **Accessible Logo**: Ensure logo URL is publicly accessible
- **Consistent Branding**: Match company branding guidelines
- **Test Display**: Verify colors and logo display correctly

---

## Troubleshooting

### Profile Not Saving

**Problem**: Changes not saving after clicking save button

**Solutions**:
- Check all required fields are filled (marked with *)
- Look for validation error messages
- Refresh page and try again
- Check browser console for errors

### AI Not Using Updated Profile

**Problem**: AI analysis doesn't reflect profile changes

**Solutions**:
- Refresh AI Framework cache (AI Framework → Refresh All Frameworks)
- Regenerate value components
- Clear browser cache
- Generate new persona to test changes

### Industries Not Generating Frameworks

**Problem**: Industry frameworks not appearing

**Solutions**:
- Verify industries are selected in company profile
- Check company profile is saved and complete
- Refresh framework cache
- Check AI Framework view for errors

### Value Components Not Generating

**Problem**: Value components not generating from profile

**Solutions**:
- Verify company profile is complete
- Check Products & Services field is filled
- Ensure Core Business Description is detailed
- Try manual value component generation

### Branding Not Applying

**Problem**: Colors and logo not showing

**Solutions**:
- Verify logo URL is publicly accessible
- Check color format is correct (hex code)
- Clear browser cache
- Refresh page

---

## Related Documentation

- **[ADMIN_GUIDE.md](ADMIN_GUIDE.md)** - Complete admin guide
- **[AI_FRAMEWORK_GUIDE.md](AI_FRAMEWORK_GUIDE.md)** - How frameworks use company profile
- **[USER_GUIDE.md](../Users/USER_GUIDE.md)** - User guide

---

<div align="center">

**Happy configuring! 🏢**

[⬆ Back to Top](#company-profile-complete-guide)

</div>

