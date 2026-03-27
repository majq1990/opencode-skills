"""
Data Classifier

智能分类钉钉文档数据为结构化/非结构化
"""

import re
import json
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DataCategory(Enum):
    """数据分类"""
    STRUCTURED = "STRUCTURED"  # 结构化数据
    UNSTRUCTURED = "UNSTRUCTURED"  # 非结构化数据
    SEMI_STRUCTURED = "SEMI_STRUCTURED"  # 半结构化数据


@dataclass
class ClassificationResult:
    """分类结果"""
    category: DataCategory
    confidence: float
    reasons: List[str]
    structured_fields: Dict = None


class DataClassifier:
    """数据分类器"""
    
    # 结构化数据特征关键词
    STRUCTURED_KEYWORDS = [
        '政策', '规定', '制度', '办法', '条例', '章程',  # 政策类
        '流程', '指南', '手册', '说明', '指引',  # 流程类
        '合同', '协议', '申请', '报告', '表格',  # 文档类
        '计划', '总结', '规划', '方案', '预算',  # 规划类
    ]
    
    # 非结构化数据特征
    UNSTRUCTURED_PATTERNS = [
        r'^#{1,6}\s+',  # Markdown 标题
        r'^- ',  # 列表
        r'^\d+\. ',  # 编号列表
        r'^> ',  # 引用
        r'\*\*.*?\*\*',  # 粗体
        r'\[.*?\]\(.*?\)',  # 链接
    ]
    
    # 结构化数据模式
    STRUCTURED_PATTERNS = [
        r'第 [一二三四五六七八九十\d]+章',  # 章节
        r'第 [一二三四五六七八九十\d]+条',  # 条款
        r'^\d+\.\d+(\.\d+)*\s+',  # 编号 1.1.1
        r'^[\(\（][一二三四五六七八九十\d]+[\)\）]',  # (一)、(1)
    ]
    
    def __init__(self):
        """初始化分类器"""
        pass
    
    def classify(self, document: Dict) -> ClassificationResult:
        """
        分类文档
        
        Args:
            document: 文档字典 (包含 metadata 和 content)
        
        Returns:
            分类结果
        """
        metadata = document.get('metadata', {})
        content = document.get('content', '')
        title = metadata.get('title', metadata.get('name', ''))
        
        # 1. 基于标题分类
        title_score, title_reasons = self._classify_by_title(title)
        
        # 2. 基于内容结构分类
        content_score, content_reasons = self._classify_by_content(content)
        
        # 3. 基于元数据分类
        meta_score, meta_reasons = self._classify_by_metadata(metadata)
        
        # 综合评分
        final_score = (title_score + content_score * 0.7 + meta_score * 0.5) / 2.2
        all_reasons = title_reasons + content_reasons + meta_reasons
        
        # 确定分类
        if final_score >= 0.7:
            category = DataCategory.STRUCTURED
        elif final_score <= 0.3:
            category = DataCategory.UNSTRUCTURED
        else:
            category = DataCategory.SEMI_STRUCTURED
        
        return ClassificationResult(
            category=category,
            confidence=final_score,
            reasons=all_reasons
        )
    
    def _classify_by_title(self, title: str) -> Tuple[float, List[str]]:
        """基于标题分类"""
        reasons = []
        score = 0.5  # 默认中性
        
        if not title:
            return 0.5, ["无标题"]
        
        # 检查结构化关键词
        for keyword in self.STRUCTURED_KEYWORDS:
            if keyword in title.lower():
                score += 0.3
                reasons.append(f"标题包含结构化关键词：{keyword}")
                break
        
        # 检查是否像会议记录/笔记
        informal_patterns = [
            r'会议记录', r'纪要', r'笔记', r'草稿', r'临时',
            r'讨论', r'想法', r'建议', r'待办'
        ]
        
        for pattern in informal_patterns:
            if re.search(pattern, title):
                score -= 0.2
                reasons.append(f"标题像非正式文档：{pattern}")
                break
        
        return min(1.0, max(0.0, score)), reasons
    
    def _classify_by_content(self, content: str) -> Tuple[float, List[str]]:
        """基于内容结构分类"""
        reasons = []
        score = 0.5
        
        if not content or len(content) < 50:
            return 0.5, ["内容太短"]
        
        # 检查结构化模式
        structured_count = 0
        for pattern in self.STRUCTURED_PATTERNS:
            if re.search(pattern, content):
                structured_count += 1
                reasons.append(f"检测到结构化模式：{pattern}")
        
        if structured_count > 0:
            score += 0.3 * min(structured_count, 3)
        
        # 检查 Markdown 格式 (倾向于非结构化)
        markdown_count = 0
        for pattern in self.UNSTRUCTURED_PATTERNS:
            if re.search(pattern, content):
                markdown_count += 1
        
        if markdown_count > 10:
            score -= 0.2
            reasons.append(f"Markdown 格式较多 ({markdown_count} 处)")
        
        # 检查段落长度 (长段落倾向于结构化)
        paragraphs = content.split('\n\n')
        if len(paragraphs) > 5:
            avg_length = sum(len(p) for p in paragraphs) / len(paragraphs)
            if avg_length > 200:
                score += 0.1
                reasons.append(f"段落平均长度较长 ({avg_length:.0f} 字符)")
        
        return min(1.0, max(0.0, score)), reasons
    
    def _classify_by_metadata(self, metadata: Dict) -> Tuple[float, List[str]]:
        """基于元数据分类"""
        reasons = []
        score = 0.5
        
        # 检查知识库类型
        kb_name = metadata.get('knowledgeBaseName', '')
        
        if any(kw in kb_name for kw in ['政策', '制度', '规定', '流程']):
            score += 0.3
            reasons.append(f"知识库类型暗示结构化：{kb_name}")
        
        if any(kw in kb_name for kw in ['会议', '讨论', '笔记']):
            score -= 0.2
            reasons.append(f"知识库类型暗示非结构化：{kb_name}")
        
        # 检查创建者 (部门文档更可能是结构化)
        creator_id = metadata.get('creatorId', '')
        if creator_id:
            score += 0.1
            reasons.append("有明确的创建者")
        
        return min(1.0, max(0.0, score)), reasons
    
    def extract_structured_fields(self, content: str) -> Dict:
        """
        从结构化内容中提取字段
        
        Args:
            content: 文档内容
        
        Returns:
            提取的字段字典
        """
        fields = {
            'chapters': [],
            'sections': [],
            'articles': [],
            'tables': []
        }
        
        # 提取章节
        chapter_pattern = r'第 ([一二三四五六七八九十\d]+) 章 [.。]?(.*?)\n'
        for match in re.finditer(chapter_pattern, content):
            fields['chapters'].append({
                'number': match.group(1),
                'title': match.group(2).strip()
            })
        
        # 提取条款
        article_pattern = r'第 ([一二三四五六七八九十\d]+) 条 [.。]?(.*?)(?=\n 第 |\Z)'
        for match in re.finditer(article_pattern, content, re.DOTALL):
            fields['articles'].append({
                'number': match.group(1),
                'content': match.group(2).strip()
            })
        
        return fields
    
    def generate_chunks(self, 
                       content: str, 
                       chunk_size: int = 500,
                       overlap: int = 50) -> List[Dict]:
        """
        将内容切分为适合向量化的块
        
        Args:
            content: 文档内容
            chunk_size: 每块大小 (字符)
            overlap: 重叠大小
        
        Returns:
            块列表
        """
        chunks = []
        
        # 尝试按段落切分
        paragraphs = content.split('\n\n')
        
        current_chunk = ""
        current_index = 0
        chunk_index = 0
        
        for i, para in enumerate(paragraphs):
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + "\n\n"
            else:
                # 保存当前块
                if current_chunk:
                    chunks.append({
                        'index': chunk_index,
                        'content': current_chunk.strip(),
                        'start_index': current_index,
                        'end_index': current_index + len(current_chunk)
                    })
                    chunk_index += 1
                    current_index += len(current_chunk)
                
                # 保留重叠部分
                if overlap > 0 and current_chunk:
                    current_chunk = current_chunk[-overlap:]
                else:
                    current_chunk = ""
                
                current_chunk += para + "\n\n"
        
        # 添加最后一块
        if current_chunk:
            chunks.append({
                'index': chunk_index,
                'content': current_chunk.strip(),
                'start_index': current_index,
                'end_index': len(content)
            })
        
        return chunks
