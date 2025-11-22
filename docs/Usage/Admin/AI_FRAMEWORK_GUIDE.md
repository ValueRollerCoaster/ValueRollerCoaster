# AI Framework: Complete Guide

<div align="center">

# 🤖

**Everything you need to know about Industry Framework generation and usage**

</div>

---

## 📋 Table of Contents

- [What is AI Framework?](#what-is-ai-framework)
- [How Frameworks Are Generated](#how-frameworks-are-generated)
- [Framework Structure](#framework-structure)
- [How Frameworks Are Used](#how-frameworks-are-used)
- [Framework Validation](#framework-validation)
- [Viewing and Managing Frameworks](#viewing-and-managing-frameworks)
- [Framework Customization](#framework-customization)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## What is AI Framework?

The **AI Framework** system generates industry-specific frameworks that enhance AI-powered analysis throughout Value Rollercoaster.

### Core Purpose

Industry Frameworks provide:
- **Industry Context**: Deep understanding of each industry you serve
- **Structured Data**: Organized industry information (metrics, trends, pain points)
- **AI Enhancement**: Improves AI analysis quality and relevance
- **Market Intelligence**: Industry-specific insights for persona generation

### Dynamic Generation

Frameworks are **dynamically generated** based on:
- **Your Company Profile**: Industries you serve, business model, market position
- **Industry Knowledge**: AI-powered industry analysis
- **NACE Classification**: European industry classification system
- **Real-Time Data**: Current industry trends and metrics

### One Framework Per Industry

For each industry in your "Industries Served" list, a unique framework is generated automatically.

---

## How Frameworks Are Generated

### Generation Process

1. **Company Profile Analysis**
   - Reads your "Industries Served" list
   - Analyzes your business model and market position
   - Understands your target customers

2. **Industry Analysis**
   - AI analyzes each industry
   - Identifies industry-specific characteristics
   - Gathers current industry data

3. **Framework Creation**
   - Generates framework structure
   - Populates framework properties
   - Applies company-specific customizations

4. **Caching**
   - Frameworks are cached for performance
   - Cache refreshes when company profile changes
   - Manual refresh available

### Automatic Generation

Frameworks are generated:
- **On First Use**: When you first access a feature requiring frameworks
- **After Profile Changes**: When company profile industries change
- **On Manual Refresh**: When you click "Refresh Framework"
- **On Cache Clear**: When framework cache is cleared

### Generation Time

- **First Generation**: 30-60 seconds per industry
- **Cached Frameworks**: Instant (from cache)
- **Refresh**: 30-60 seconds per industry

---

## Framework Structure

Each framework contains **9 key properties**:

### 1. Industry Name
- **Type**: String
- **Purpose**: Display name of the industry
- **Example**: "Mining", "Construction", "Manufacturing"

### 2. NACE Codes
- **Type**: Array of strings
- **Purpose**: European industry classification codes
- **Used In**: Industry classification, market intelligence
- **Example**: ["B05.10", "B05.20"]
- **Source**: NACE classification system

### 3. Key Metrics
- **Type**: Array of strings
- **Purpose**: Industry-specific performance metrics
- **Used In**: Market intelligence, persona generation
- **Example**: ["Production Volume", "Safety Incidents", "Equipment Utilization"]
- **Source**: Industry analysis

### 4. Trend Areas
- **Type**: Array of strings
- **Purpose**: Current industry trends
- **Used In**: Market intelligence, strategic recommendations
- **Example**: ["Digitalization", "Sustainability", "Automation"]
- **Source**: Industry trend analysis

### 5. Value Drivers
- **Type**: Array of strings
- **Purpose**: What drives value in this industry
- **Used In**: Value alignment, persona generation
- **Example**: ["Cost Efficiency", "Reliability", "Safety"]
- **Source**: Industry value analysis

### 6. Pain Points
- **Type**: Array of strings
- **Purpose**: Common industry challenges
- **Used In**: Persona generation, value alignment
- **Example**: ["High Maintenance Costs", "Safety Concerns", "Regulatory Compliance"]
- **Source**: Industry challenge analysis

### 7. Competitive Factors
- **Type**: Array of strings
- **Purpose**: Key competitive differentiators
- **Used In**: Competitive analysis, value alignment
- **Example**: ["Technology Innovation", "Service Quality", "Price"]
- **Source**: Competitive landscape analysis

### 8. Technology Focus
- **Type**: Array of strings
- **Purpose**: Technology trends and adoption
- **Used In**: Market intelligence, technology recommendations
- **Example**: ["IoT Integration", "Predictive Maintenance", "Automation"]
- **Source**: Technology trend analysis

### 9. Sustainability Initiatives
- **Type**: Array of strings
- **Purpose**: Sustainability trends and initiatives
- **Used In**: Market intelligence, value alignment
- **Example**: ["Carbon Reduction", "Circular Economy", "Renewable Energy"]
- **Source**: Sustainability trend analysis

---

## How Frameworks Are Used

### 1. Market Intelligence Generation

Frameworks provide industry context for market intelligence:

```
INDUSTRY FRAMEWORK:
  Industry: Mining
  NACE Codes: B05.10, B05.20
  Key Metrics: Production Volume, Safety Incidents
  Trend Areas: Digitalization, Sustainability
  Value Drivers: Cost Efficiency, Reliability
  Pain Points: High Maintenance Costs, Safety Concerns
  ...
```

This context helps AI generate **industry-relevant** market intelligence.

### 2. Persona Generation

Frameworks enhance persona generation by:
- **Industry Context**: Understanding prospect's industry
- **Pain Points**: Identifying industry-specific challenges
- **Value Drivers**: Understanding what prospects value
- **Trends**: Providing current industry context

### 3. Value Alignment

Frameworks improve value alignment by:
- **Industry-Specific Matching**: Matching your values with industry needs
- **Pain Point Alignment**: Aligning with industry challenges
- **Value Driver Focus**: Emphasizing industry-relevant values
- **Trend Integration**: Incorporating current industry trends

### 4. AI Prompt Enhancement

Frameworks are embedded in AI prompts to provide:
- **Industry Expertise**: AI acts as industry expert
- **Relevant Analysis**: Analysis focused on industry specifics
- **Current Context**: Up-to-date industry information
- **Structured Data**: Organized industry knowledge

---

## Framework Validation

### What is Validation?

Framework validation checks framework **quality, completeness, and relevance** using AI-powered analysis.

### Validation Process

1. **Relevance Check**: Are framework properties relevant to the industry?
2. **Completeness Check**: Are all critical elements present?
3. **Consistency Check**: Are properties consistent with each other?
4. **Quality Scoring**: Overall quality score (0-100)

### Validation Results

Validation provides:
- **Overall Quality Score**: 0-100 (higher is better)
- **Relevance Scores**: Per-property relevance scores
- **Completeness Score**: How complete the framework is
- **Issues List**: Specific issues found
- **AI Refinements**: Suggested improvements

### Quality Score Interpretation

- **80-100**: Excellent - Framework is high quality
- **60-79**: Good - Framework is usable, minor improvements possible
- **40-59**: Needs Improvement - Framework has significant issues
- **0-39**: Poor - Framework needs major revision

### How to Validate

1. Go to **🔧 Admin Tools** → **🤖 AI Framework**
2. Select an industry
3. Click **🔍 Validate** button
4. Wait for validation (30-60 seconds)
5. Review validation results

### Applying Refinements

If validation suggests refinements:
1. Review suggested refinements
2. Click **✅ Apply AI Refinements** (if available)
3. Refinements are applied automatically
4. Re-validate to check improvement

---

## Viewing and Managing Frameworks

### Accessing Framework View

1. **Login as Admin**: Use `default_user` account
2. **Go to Admin Tools**: Click **🔧 Admin Tools** in sidebar
3. **Open AI Framework**: Click **🤖 AI Framework**
4. **Select Industry**: Choose industry from dropdown

### Framework View Tabs

#### 1. Overview Dashboard
- **Summary Statistics**: Total industries, average metrics, NACE coverage
- **Quality Dashboard**: Quality scores if validated
- **Industry List**: All industries with frameworks
- **Quick Actions**: Refresh, export options

#### 2. Industry Frameworks
- **Framework Selection**: Select industry to view
- **Framework Properties**: All 9 framework properties
- **Validation Status**: Quality scores and validation results
- **Framework Actions**: Refresh, validate, export

#### 3. Company Context
- **Company Profile Summary**: How your profile influences frameworks
- **Industry Mapping**: Your industries and their frameworks
- **Customization Indicators**: What's customized vs. generic

### Framework Actions

#### Refresh Framework
- **What it does**: Clears cache and regenerates framework
- **When to use**: After company profile changes, if framework seems outdated
- **How**: Click **🔄 Refresh Framework** button

#### Validate Framework
- **What it does**: Validates framework quality and completeness
- **When to use**: Periodically, after changes, before important analysis
- **How**: Click **🔍 Validate** button

#### Export Framework
- **What it does**: Downloads framework data as JSON
- **When to use**: For analysis, backup, documentation
- **How**: Click **📥 Export Data** button

---

## Framework Customization

### Automatic Customization

Frameworks are automatically customized based on:
- **Your Company Profile**: Business model, market position, target customers
- **Your Industries**: Industries you serve
- **Your Business Model**: How you operate

### Customization Indicators

Framework view shows:
- **Generic Elements**: Standard industry information
- **Customized Elements**: Information tailored to your business
- **Company-Specific**: Information derived from your company profile

### Manual Customization

Currently, frameworks are generated automatically. Manual customization may be available in future versions.

---

## Best Practices

### Framework Generation

- **Complete Company Profile**: Ensure company profile is complete before generating frameworks
- **Accurate Industries**: Select all industries you actually serve
- **Regular Updates**: Update company profile when industries change
- **Refresh After Changes**: Refresh frameworks after profile changes

### Framework Validation

- **Regular Validation**: Validate frameworks periodically (monthly recommended)
- **Before Important Analysis**: Validate before generating important personas
- **After Profile Changes**: Validate after major company profile changes
- **Review Quality Scores**: Monitor quality scores over time

### Framework Usage

- **Trust the Framework**: Frameworks are AI-generated and validated
- **Review Validation Results**: Check validation results for quality
- **Apply Refinements**: Apply AI-suggested refinements when available
- **Export for Analysis**: Export frameworks for business analysis

### Framework Management

- **Monitor Quality**: Track quality scores across industries
- **Refresh Regularly**: Refresh frameworks quarterly or after major changes
- **Export Backups**: Export frameworks for backup
- **Document Changes**: Keep records of framework updates

---

## Troubleshooting

### Frameworks Not Generating

**Problem**: No frameworks appear in AI Framework view

**Solutions**:
- Check company profile has industries configured
- Verify company profile is saved and complete
- Refresh page and try again
- Check for error messages in console

### Framework Generation Failing

**Problem**: Framework generation errors or timeouts

**Solutions**:
- Check API keys are configured correctly
- Verify company profile is complete
- Try refreshing individual framework
- Check network connection

### Validation Failing

**Problem**: Framework validation errors or timeouts

**Solutions**:
- Check API keys are configured correctly
- Verify framework has data
- Try refreshing framework first
- Check validation button is enabled

### Low Quality Scores

**Problem**: Framework validation shows low quality scores

**Solutions**:
- Review validation issues list
- Apply AI-suggested refinements
- Update company profile with more detail
- Refresh framework and re-validate

### Frameworks Not Updating

**Problem**: Framework changes not reflecting after profile update

**Solutions**:
- Refresh framework cache (Refresh All Frameworks)
- Clear browser cache
- Verify company profile changes were saved
- Try manual refresh of specific framework

### Missing Framework Properties

**Problem**: Some framework properties are empty or missing

**Solutions**:
- Check company profile completeness
- Verify industries are correctly configured
- Refresh framework
- Validate framework to identify issues

---

## Understanding Framework Data Flow

```
Company Profile
    ↓
Industries Served List
    ↓
Framework Generator
    ↓
Industry Analysis (AI)
    ↓
Framework Structure
    ↓
Framework Properties (9 properties)
    ↓
Framework Cache
    ↓
AI Prompts (Market Intelligence, Persona Generation, Value Alignment)
```

---

## Related Documentation

- **[ADMIN_GUIDE.md](ADMIN_GUIDE.md)** - Complete admin guide
- **[COMPANY_PROFILE_GUIDE.md](COMPANY_PROFILE_GUIDE.md)** - How company profile affects frameworks
- **[USER_GUIDE.md](../Users/USER_GUIDE.md)** - User guide

---

<div align="center">

**Happy framework managing! 🤖**

[⬆ Back to Top](#ai-framework-complete-guide)

</div>

