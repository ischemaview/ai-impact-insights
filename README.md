# AI Impact Insights

A comprehensive framework and toolkit for measuring the impact of AI tools on engineering team performance.

## 🚀 Quick Start

1. **Clone and setup:**
   ```bash
   git clone https://github.com/your-org/ai-impact-insights.git
   cd ai-impact-insights
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure your analysis:**
   ```bash
   cp config.json.example config.json
   # Edit config.json with your GitHub token and organization details
   ```

3. **Run productivity analysis:**
   ```bash
   # For basic analysis (works with any GitHub token)
   python scripts/productivity_analyzer_fine_grained.py

   # For detailed line changes analysis
   python scripts/enhanced_line_changes_analyzer.py

   # To test Copilot API access
   python scripts/test_copilot_api.py
   ```

## 📊 What You'll Get

### Individual Developer Insights
- **Before/After productivity comparison** for the same developers
- **Commits per week improvement** percentages
- **Lines of code changes** analysis
- **AI assistance adoption** patterns

### Team-Level Metrics
- **Overall productivity improvements**
- **Repository activity changes**
- **Top performer identification**
- **ROI calculations**

### Example Results
```
TOP PERFORMERS (Commits per week improvement):
  developer-a: 1.0 → 4.1 commits/week (+312.5%)
  developer-b: 5.0 → 12.8 commits/week (+155.0%)
  
Overall Team: +29.9% average improvement in commits per week
Line Changes: +38.4% more code work with +46% more substantial commits
```

## 🔧 Features

- **Multiple Analysis Scripts**:
  - Basic productivity analysis (fine-grained token compatible)
  - Enhanced line changes analysis
  - Copilot-specific metrics (when API access available)

- **Flexible Configuration**:
  - Customizable analysis periods
  - Multiple repository support
  - Configurable adoption dates

- **Comprehensive Output**:
  - Human-readable summaries
  - Detailed JSON reports
  - Individual developer breakdowns

## 📋 Requirements

- Python 3.8+
- GitHub token with repository access
- Access to organization repositories you want to analyze

## 🔐 Token Permissions

### Fine-Grained Personal Access Token (Recommended)
**Repository permissions:**
- Contents: `Read`
- Metadata: `Read`
- Pull requests: `Read` (optional)

**Organization permissions** (for Copilot API access):
- "GitHub Copilot Business": `Read` OR "Administration": `Read`

### Classic Personal Access Token
- `repo` (Full control of private repositories)  
- `read:org` (Read organization data)

## 📁 Project Structure

```
├── docs/                   # Documentation and frameworks
│   ├── metrics-framework.md
│   ├── implementation-guide.md
│   └── token-permissions.md
├── scripts/               # Analysis scripts
│   ├── productivity_analyzer_fine_grained.py
│   ├── enhanced_line_changes_analyzer.py
│   └── test_copilot_api.py
├── templates/             # Survey and configuration templates
├── examples/              # Example outputs and case studies
├── config.json.example    # Configuration template
└── requirements.txt       # Python dependencies
```

## 🎯 Use Cases

### For Engineering Managers
- **ROI measurement** of AI tool investments
- **Team performance tracking** over time
- **Individual developer coaching** insights
- **Budget justification** for AI tools

### For Team Leads  
- **Identify top performers** and best practices
- **Understand AI tool adoption** patterns
- **Optimize team workflows** based on data
- **Track productivity trends**

### For Organizations
- **Compare teams/departments** AI adoption success
- **Strategic planning** for AI tool rollouts
- **Benchmark productivity** improvements
- **Data-driven decision making**

## 📈 Analysis Types

### 1. Before/After Comparison
Compare the same developers' productivity before and after AI tool adoption.

### 2. Repository Activity Analysis  
Track changes in commit patterns, code volume, and development velocity.

### 3. Individual Performance Tracking
Identify which developers benefit most from AI tools and understand usage patterns.

### 4. Team-Level Insights
Aggregate individual improvements into team and organizational metrics.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 Check the [Documentation](./docs/) for detailed guides
- 🐛 Report issues in GitHub Issues
- 💬 Start discussions for questions and ideas

## 🎉 Example Success Story

> "After implementing AI tools in July 2024, our team showed a **29.9% average improvement** in commits per week, with some developers seeing **300%+ productivity gains**. The total line changes increased by **38.4%** while maintaining code quality."

---

**Ready to measure your AI impact?** Start with the [Setup Guide](./SETUP.md)!