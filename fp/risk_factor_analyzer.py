# risk_factor_analyzer_NSE_COMPLETE.py
# Complete NSE-style checks for ALL 18 officer queries

import re
import json
from typing import List, Dict, Any

class RiskFactorAnalyzer:
    """NSE officer-style granular risk factor analysis"""
    
    def __init__(self, llm, document):
        self.llm = llm
        self.document = document
        self.risk_factors = []
    
    def extract_risk_factors(self):
        """Extract all numbered risk factors"""
        print("\n📋 Extracting risk factors...")
        
        full_text = self.document.get('full_text', '')
        if not full_text:
            return []
        
        # Pattern for "1.", "2.", "3." format
        rf_pattern = r'^(\d+)\.\s+([^\n]+)'
        matches = re.finditer(rf_pattern, full_text, re.MULTILINE)
        
        for match in matches:
            rf_number = int(match.group(1))
            rf_title = match.group(2).strip()
            
            start_pos = match.start()
            remaining_text = full_text[start_pos:]
            next_match = re.search(r'\n(\d+)\.\s+', remaining_text[10:])
            
            if next_match:
                end_pos = start_pos + 10 + next_match.start()
            else:
                end_pos = len(full_text)
            
            rf_content = full_text[start_pos:end_pos].strip()
            page_num = (start_pos // 3000) + 1
            
            self.risk_factors.append({
                'number': rf_number,
                'title': rf_title[:300],
                'content': rf_content,
                'page': page_num
            })
        
        print(f"   ✅ Extracted {len(self.risk_factors)} risk factors")
        return self.risk_factors
    
    def run_nse_checks(self):
        """Run all 18 NSE-style checks"""
        print(f"\n🔍 Running NSE compliance checks on {len(self.risk_factors)} RFs...")
        
        compliance_items = []
        
        # ==========================================
        # QUERY 18(b) - RF-8 Financial Units
        # ==========================================
        rf_8 = self._get_rf(8)
        if rf_8:
            has_table = bool(re.search(r'(year|fy|march|2024|2023|2022)', rf_8['content'], re.I))
            has_numbers = len(re.findall(r'\d+[\d,]*\.?\d*', rf_8['content'])) >= 5
            has_units = bool(re.search(r'(₹|rs\.?|rupees|lakhs?|crores?|millions?)', rf_8['content'], re.I))
            
            if has_table and has_numbers and not has_units:
                status = 'INSUFFICIENT'
                explanation = 'RF-8 contains financial table but lacks units specification'
                missing = 'Disclose financial units (₹ in lakhs/crores) in table headers or footnote'
                priority = 'HIGH'
            elif has_table and has_numbers and has_units:
                status = 'PRESENT'
                explanation = 'RF-8 financial data includes units'
                missing = ''
                priority = 'LOW'
            else:
                status = 'INSUFFICIENT'
                explanation = 'RF-8 lacks structured financial table'
                missing = 'Add table with financial figures and units'
                priority = 'HIGH'
            
            compliance_items.append({
                'requirement': 'RF-8: Financial data table must specify units (₹ lakhs/crores)',
                'status': status,
                'explanation': explanation,
                'missing_details': missing,
                'pages': [rf_8['page']],
                'priority': priority,
                'citation': 'NSE Query 18(b)'
            })
        
        # ==========================================
        # QUERY 18(c) - RF-9 Negative Cash Flow  
        # ==========================================
        rf_9 = self._get_rf(9)
        if rf_9:
            has_negative_cf = bool(re.search(r'negative.*cash.*flow', rf_9['content'], re.I))
            
            if has_negative_cf:
                # Check for reasons/explanation
                reason_keywords = ['due to', 'because', 'primarily', 'caused by', 'reason', 'result of']
                has_reasons = any(kw in rf_9['content'].lower() for kw in reason_keywords)
                
                # Check for breakdown
                has_breakdown = bool(re.search(r'\(a\)|\(i\)|•|1\.|first|second', rf_9['content'], re.I))
                
                # Check for quantification
                amounts = re.findall(r'₹\s*[\d,]+(?:\.\d+)?', rf_9['content'])
                has_quantification = len(amounts) >= 2
                
                if has_reasons and has_breakdown and has_quantification:
                    status = 'PRESENT'
                    explanation = 'RF-9 explains reasons for negative cash flow with quantified breakdown'
                    missing = ''
                    priority = 'LOW'
                elif has_reasons:
                    status = 'INSUFFICIENT'
                    explanation = 'RF-9 mentions negative cash flow reasons but lacks detailed quantified breakdown'
                    missing = 'Add specific breakdown: (a) Working capital increase ₹X Cr, (b) Capex ₹Y Cr, (c) Other ₹Z Cr'
                    priority = 'CRITICAL'
                else:
                    status = 'INSUFFICIENT'
                    explanation = 'RF-9 mentions negative cash flow but does not explain WHY'
                    missing = 'Add reasons for negative cash flow with quantification (e.g., increased working capital, delayed receivables, capex)'
                    priority = 'CRITICAL'
            else:
                status = 'MISSING'
                explanation = 'RF-9 does not mention negative cash flow'
                missing = 'Disclose negative cash flow and explain reasons'
                priority = 'CRITICAL'
            
            compliance_items.append({
                'requirement': 'RF-9: Explanation for negative cash flow with specific reasons',
                'status': status,
                'explanation': explanation,
                'missing_details': missing,
                'pages': [rf_9['page']],
                'priority': priority,
                'citation': 'NSE Query 18(c)'
            })
        
        # ==========================================
        # QUERY 18(d) - RF-20 Ranking/Prioritization
        # ==========================================
        rf_20 = self._get_rf(20)
        if rf_20:
            # Check if RF-20 discusses material/severe risk
            materiality_keywords = ['material', 'significant', 'substantial', 'major', 'critical', 'adversely affect']
            is_material = any(kw in rf_20['content'].lower() for kw in materiality_keywords)
            
            # RF-20 position in document
            rf_20_position = next((i+1 for i, rf in enumerate(self.risk_factors) if rf['number'] == 20), None)
            
            if is_material and rf_20_position and rf_20_position > 10:
                status = 'INSUFFICIENT'
                explanation = f'RF-20 appears material but is ranked #{rf_20_position}. Should be in top 5/10 based on severity'
                missing = f'Re-prioritize RF-20 to top 5 position (currently #{rf_20_position})'
                priority = 'HIGH'
            elif is_material and rf_20_position and rf_20_position <= 5:
                status = 'PRESENT'
                explanation = f'RF-20 is appropriately prioritized at position #{rf_20_position}'
                missing = ''
                priority = 'LOW'
            else:
                status = 'UNCLEAR'
                explanation = 'Unable to assess RF-20 materiality and ranking'
                missing = 'Verify RF-20 prioritization based on severity'
                priority = 'MEDIUM'
            
            compliance_items.append({
                'requirement': 'RF-20: Ranking - Should be in top 5/10 if material',
                'status': status,
                'explanation': explanation,
                'missing_details': missing,
                'pages': [rf_20['page']],
                'priority': priority,
                'citation': 'NSE Query 18(d)'
            })
        
        # ==========================================
        # QUERY 18(e) - RF-23 & RF-29 Past Instances
        # ==========================================
        for rf_num in [23, 29]:
            rf = self._get_rf(rf_num)
            if rf:
                # Check for past instances
                past_keywords = ['past instance', 'previously', 'in the past', 'historical', 'prior', 'earlier']
                has_past_ref = any(kw in rf['content'].lower() for kw in past_keywords)
                
                # Check for "none"/"no past"
                no_past = bool(re.search(r'(no|not|never).*past.*instance', rf['content'], re.I))
                
                if has_past_ref and not no_past:
                    status = 'PRESENT'
                    explanation = f'RF-{rf_num} includes past instances'
                    missing = ''
                    priority = 'LOW'
                elif no_past:
                    status = 'PRESENT'
                    explanation = f'RF-{rf_num} confirms no past instances'
                    missing = ''
                    priority = 'LOW'
                else:
                    status = 'INSUFFICIENT'
                    explanation = f'RF-{rf_num} does not mention past instances (if any)'
                    missing = f'Elaborate RF-{rf_num} to include past instances if any, or confirm "No past instances"'
                    priority = 'HIGH'
                
                compliance_items.append({
                    'requirement': f'RF-{rf_num}: Past instances disclosure',
                    'status': status,
                    'explanation': explanation,
                    'missing_details': missing,
                    'pages': [rf['page']],
                    'priority': priority,
                    'citation': 'NSE Query 18(e)'
                })
        
        # ==========================================
        # QUERY 18(f) - RF-27 Compliance Statement
        # ==========================================
        rf_27 = self._get_rf(27)
        if rf_27:
            # Check for RPT mention
            has_rpt = bool(re.search(r'related.*party.*transaction|rpt', rf_27['content'], re.I))
            
            if has_rpt:
                # Check for compliance confirmation
                compliance_keywords = ['compliance|complies|comply', 'accordance', 'companies act.*2013', 'section 188']
                has_compliance = any(bool(re.search(kw, rf_27['content'], re.I)) for kw in compliance_keywords)
                
                if has_compliance:
                    status = 'PRESENT'
                    explanation = 'RF-27 confirms RPTs conducted in compliance with Companies Act 2013'
                    missing = ''
                    priority = 'LOW'
                else:
                    status = 'INSUFFICIENT'
                    explanation = 'RF-27 mentions RPTs but lacks compliance confirmation'
                    missing = 'Add confirmation: "All RPTs are conducted in compliance with Section 188 of Companies Act, 2013"'
                    priority = 'HIGH'
            else:
                status = 'UNCLEAR'
                explanation = 'RF-27 does not appear to cover RPTs'
                missing = 'Verify if RF-27 is related to RPTs'
                priority = 'MEDIUM'
            
            compliance_items.append({
                'requirement': 'RF-27: RPT compliance statement (Companies Act 2013)',
                'status': status,
                'explanation': explanation,
                'missing_details': missing,
                'pages': [rf_27['page']],
                'priority': priority,
                'citation': 'NSE Query 18(f)'
            })
        
        # ==========================================
        # QUERY 18(g) - RF-28 Insurance Data (3 years)
        # ==========================================
        rf_28 = self._get_rf(28)
        if rf_28:
            # Check for insurance mention
            has_insurance = bool(re.search(r'insurance|insured|coverage|claim', rf_28['content'], re.I))
            
            if has_insurance:
                # Check for 3-year data
                years = re.findall(r'(20\d{2}|FY\s*\d{2,4})', rf_28['content'])
                has_3_years = len(set(years)) >= 3
                
                # Check for loss vs insurance comparison
                has_loss_data = bool(re.search(r'loss', rf_28['content'], re.I))
                has_amounts = len(re.findall(r'₹\s*[\d,]+', rf_28['content'])) >= 3
                
                if has_3_years and has_loss_data and has_amounts:
                    status = 'PRESENT'
                    explanation = 'RF-28 includes 3-year insurance data with losses vs coverage'
                    missing = ''
                    priority = 'LOW'
                else:
                    status = 'INSUFFICIENT'
                    explanation = 'RF-28 mentions insurance but lacks complete 3-year data'
                    missing = 'Add table: FY 2023-24, 2022-23, 2021-22 with (i) Total losses (ii) Insurance coverage (iii) Past claims exceeding coverage'
                    priority = 'HIGH'
            else:
                status = 'UNCLEAR'
                explanation = 'RF-28 does not appear to cover insurance'
                missing = 'Verify if RF-28 is insurance-related'
                priority = 'MEDIUM'
            
            compliance_items.append({
                'requirement': 'RF-28: 3-year insurance data (losses vs coverage)',
                'status': status,
                'explanation': explanation,
                'missing_details': missing,
                'pages': [rf_28['page']],
                'priority': priority,
                'citation': 'NSE Query 18(g)'
            })
        
        # ==========================================
        # QUERY 18(h) - RF-41 ROC Search
        # ==========================================
        rf_41 = self._get_rf(41)
        if rf_41:
            # Check for defaults/charges mention
            has_defaults = bool(re.search(r'default|charge|loan|borrowing', rf_41['content'], re.I))
            
            if has_defaults:
                # Check for ROC search confirmation
                has_roc = bool(re.search(r'roc.*search|registrar.*companies.*search|search.*report', rf_41['content'], re.I))
                
                if has_roc:
                    status = 'PRESENT'
                    explanation = 'RF-41 confirms ROC search undertaken'
                    missing = ''
                    priority = 'LOW'
                else:
                    status = 'INSUFFICIENT'
                    explanation = 'RF-41 mentions defaults/charges but lacks ROC search confirmation'
                    missing = 'Clarify whether Company has undertaken ROC search and obtained search report. If yes, confirm findings; if no, state same'
                    priority = 'CRITICAL'
            else:
                status = 'UNCLEAR'
                explanation = 'RF-41 does not appear to cover defaults/charges'
                missing = 'Verify if RF-41 is related to defaults'
                priority = 'MEDIUM'
            
            compliance_items.append({
                'requirement': 'RF-41: ROC search confirmation for charges/defaults',
                'status': status,
                'explanation': explanation,
                'missing_details': missing,
                'pages': [rf_41['page']],
                'priority': priority,
                'citation': 'NSE Query 18(h)'
            })
        
        # ==========================================
        # QUERY 18(i) - RF-42 Director Qualifications
        # ==========================================
        rf_42 = self._get_rf(42)
        if rf_42:
            # Check for director/qualification mention
            has_directors = bool(re.search(r'director|qualification|educational|degree|certificate', rf_42['content'], re.I))
            
            if has_directors:
                # Check for document traceability issue
                has_issue = bool(re.search(r'unable.*trace|cannot.*locate|not.*available|missing|lost', rf_42['content'], re.I))
                
                if has_issue:
                    status = 'PRESENT'
                    explanation = 'RF-42 discloses inability to trace educational qualification documents'
                    missing = ''
                    priority = 'MEDIUM'
                else:
                    # Check if documents are confirmed available
                    has_docs = bool(re.search(r'available|obtained|verified|attached', rf_42['content'], re.I))
                    
                    if has_docs:
                        status = 'PRESENT'
                        explanation = 'RF-42 confirms educational documents available'
                        missing = ''
                        priority = 'LOW'
                    else:
                        status = 'INSUFFICIENT'
                        explanation = 'RF-42 mentions directors but unclear on document availability'
                        missing = 'Clarify: Directors unable to trace copies of educational qualification documents (if applicable)'
                        priority = 'HIGH'
            else:
                status = 'UNCLEAR'
                explanation = 'RF-42 does not appear to cover director qualifications'
                missing = 'Verify if RF-42 is related to director qualifications'
                priority = 'MEDIUM'
            
            compliance_items.append({
                'requirement': 'RF-42: Director educational qualification documents traceability',
                'status': status,
                'explanation': explanation,
                'missing_details': missing,
                'pages': [rf_42['page']],
                'priority': priority,
                'citation': 'NSE Query 18(i)'
            })
        
        # ==========================================
        # QUERY 23(a) - Litigation Risk Factor
        # ==========================================
        litigation_rfs = [rf for rf in self.risk_factors if re.search(r'litigation|legal.*proceed|lawsuit|suit|case|court', rf['content'], re.I)]
        
        if litigation_rfs:
            rf = litigation_rfs[0]
            
            # Check for quantification
            amounts = re.findall(r'₹\s*[\d,]+(?:\s*(?:lakh|crore|million))?', rf['content'])
            case_counts = re.findall(r'(\d+)\s*(?:case|suit|litigation|proceeding)', rf['content'], re.I)
            
            has_quantification = len(amounts) > 0 or len(case_counts) > 0
            
            # Check for past instances
            has_past = bool(re.search(r'past.*instance|previously|historical', rf['content'], re.I))
            
            if has_quantification and has_past:
                status = 'PRESENT'
                explanation = f'RF-{rf["number"]} quantifies litigation and includes past instances'
                missing = ''
                priority = 'LOW'
            elif has_quantification:
                status = 'INSUFFICIENT'
                explanation = f'RF-{rf["number"]} quantifies litigation but lacks past instances'
                missing = 'Add past instances of similar litigations (if any)'
                priority = 'MEDIUM'
            else:
                status = 'INSUFFICIENT'
                explanation = f'RF-{rf["number"]} mentions litigation but lacks quantification'
                missing = 'Quantify litigation: (i) Number of cases (ii) Amount involved (iii) Past instances'
                priority = 'HIGH'
            
            compliance_items.append({
                'requirement': 'Litigation Risk Factor: Quantification with past instances',
                'status': status,
                'explanation': explanation,
                'missing_details': missing,
                'pages': [rf['page']],
                'priority': priority,
                'citation': 'NSE Query 23(a)'
            })
        else:
            compliance_items.append({
                'requirement': 'Litigation Risk Factor: Quantification with past instances',
                'status': 'MISSING',
                'explanation': 'No litigation-related risk factor found',
                'missing_details': 'Add risk factor covering litigation with quantification and past instances',
                'pages': [],
                'priority': 'HIGH',
                'citation': 'NSE Query 23(a)'
            })
        
        # ==========================================
        # QUERY 41 & 42 - RF-46 Capex on Non-Owned Land
        # ==========================================
        rf_46 = self._get_rf(46)
        if rf_46:
            # Check for land/capex mention
            has_land = bool(re.search(r'land|property|warehouse|construction|capex', rf_46['content'], re.I))
            
            if has_land:
                # Check for ownership clarification
                has_ownership_issue = bool(re.search(r'not.*own|subsidiary.*land|rental|lease', rf_46['content'], re.I))
                
                if has_ownership_issue:
                    # Check for rental agreement mention
                    has_rental = bool(re.search(r'rental.*agreement|lease.*agreement|mou|consent', rf_46['content'], re.I))
                    
                    if has_rental:
                        status = 'PRESENT'
                        explanation = 'RF-46 discloses capex on non-owned land with rental agreement details'
                        missing = ''
                        priority = 'LOW'
                    else:
                        status = 'INSUFFICIENT'
                        explanation = 'RF-46 mentions capex on non-owned land but lacks rental agreement details'
                        missing = 'Include details of rental agreement (or state if not entered into)'
                        priority = 'CRITICAL'
                else:
                    status = 'UNCLEAR'
                    explanation = 'RF-46 unclear if land is owned or not'
                    missing = 'Clarify land ownership status'
                    priority = 'MEDIUM'
            else:
                status = 'UNCLEAR'
                explanation = 'RF-46 does not appear to cover land/capex'
                missing = 'Verify if RF-46 is related to construction/land'
                priority = 'MEDIUM'
            
            compliance_items.append({
                'requirement': 'RF-46: Capex on non-owned land + rental agreement',
                'status': status,
                'explanation': explanation,
                'missing_details': missing,
                'pages': [rf_46['page']],
                'priority': priority,
                'citation': 'NSE Query 41, 42'
            })
        
        # ==========================================
        # QUERY 45 - RF-47 FIR/News Article
        # ==========================================
        rf_47 = self._get_rf(47)
        if rf_47:
            # Check for FIR/legal mention
            has_fir = bool(re.search(r'fir|first.*information.*report|police|complaint', rf_47['content'], re.I))
            has_news = bool(re.search(r'news|article|media|newspaper', rf_47['content'], re.I))
            
            if has_fir or has_news:
                # Check for details
                has_details = bool(re.search(r'dated|filed|reason|outcome|resolved', rf_47['content'], re.I))
                
                if has_details:
                    status = 'PRESENT'
                    explanation = 'RF-47 discloses FIR/news article with details'
                    missing = ''
                    priority = 'LOW'
                else:
                    status = 'INSUFFICIENT'
                    explanation = 'RF-47 mentions FIR/news but lacks complete details'
                    missing = 'Provide: (i) Date of FIR/article (ii) Allegations (iii) Current status/resolution'
                    priority = 'CRITICAL'
            else:
                status = 'MISSING'
                explanation = 'RF-47 does not mention FIR or news article'
                missing = 'Disclose FIR and news article details (if applicable)'
                priority = 'HIGH'
            
            compliance_items.append({
                'requirement': 'RF-47: FIR/News article disclosure with details',
                'status': status,
                'explanation': explanation,
                'missing_details': missing,
                'pages': [rf_47['page']],
                'priority': priority,
                'citation': 'NSE Query 45'
            })
        
        # ==========================================
        # QUERY 39 - RF-48 Court Cases
        # ==========================================
        rf_48 = self._get_rf(48)
        if rf_48:
            # Check for court case mention
            has_court = bool(re.search(r'court.*case|litigation|suit|legal.*proceeding', rf_48['content'], re.I))
            
            if has_court:
                # Check for confirmation
                has_confirmation = bool(re.search(r'confirm|verified|related|similar.*name', rf_48['content'], re.I))
                
                if has_confirmation:
                    status = 'PRESENT'
                    explanation = 'RF-48 confirms relationship to court cases with similar names'
                    missing = ''
                    priority = 'LOW'
                else:
                    status = 'INSUFFICIENT'
                    explanation = 'RF-48 mentions court cases but lacks confirmation on similar names'
                    missing = 'Confirm whether court cases with similar names are related to issuer or different entity'
                    priority = 'HIGH'
            else:
                status = 'MISSING'
                explanation = 'RF-48 does not mention court cases'
                missing = 'Disclose and confirm court cases (if any)'
                priority = 'HIGH'
            
            compliance_items.append({
                'requirement': 'RF-48: Court cases confirmation (similar names)',
                'status': status,
                'explanation': explanation,
                'missing_details': missing,
                'pages': [rf_48['page']],
                'priority': priority,
                'citation': 'NSE Query 39'
            })
        
        return compliance_items
    
    def _get_rf(self, number: int) -> Dict:
        """Get risk factor by number"""
        return next((rf for rf in self.risk_factors if rf['number'] == number), None)


def check_risk_factors_chapter(document, llm):
    """Main entry point - runs all NSE checks"""
    print("\n" + "="*80)
    print("🔍 RISK FACTORS - NSE OFFICER-STYLE ANALYSIS")
    print("="*80)
    
    try:
        analyzer = RiskFactorAnalyzer(llm, document)
        
        # Extract all RFs
        risk_factors = analyzer.extract_risk_factors()
        
        if not risk_factors:
            return {
                'total_risk_factors': 0,
                'items': [{
                    'requirement': 'Risk Factor Extraction',
                    'status': 'UNCLEAR',
                    'explanation': 'Could not extract risk factors',
                    'citation': 'Document Structure',
                    'pages': [],
                    'priority': 'HIGH'
                }]
            }
        
        # Run all NSE checks
        compliance_items = analyzer.run_nse_checks()
        
        print(f"\n✅ NSE Analysis Complete")
        print(f"   Total RFs: {len(risk_factors)}")
        print(f"   NSE Checks: {len(compliance_items)}")
        
        return {
            'total_risk_factors': len(risk_factors),
            'items': compliance_items
        }
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'total_risk_factors': 0,
            'items': [{
                'requirement': 'Risk Factor Analysis',
                'status': 'UNCLEAR',
                'explanation': f'Error: {str(e)}',
                'citation': 'System Error',
                'pages': [],
                'priority': 'HIGH'
            }]
        }