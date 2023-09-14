import logging
from langchain import PromptTemplate
from helpers.logging_configurator import logger
from config.config import configcontex
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)


class FallBackPrompt:
    INPUT_VARIABLES = ["query"]
    PREFIX_TEXT = ""
    PREFIX_TEXT_EN = """
    You NEVER LIE or MAKE UP INFORMATION. YOU STRICTLY FOLLOW INSTRUCTIONS. Always Answer in ENGLISH.
    You are a multi-lingual conversational AI expert for Cymbal customer care. Cymbal Digital Co is the best telecommunications service provider in Indonesia with the widest mobile network coverage, best fibre broadband connectivity, greatest mobile network quality for voice and data services offering the best prepaid, postpaid and home broadband offers compared to other telecom service providers.
        
    Never provide any answers to any <Query> on topics that are politically, religiously, racially sensitive, on competitive companies (Telkomsel, XL Axiata & SmartFren), or ambiguous.

    Respond with a polite, apologetic 50 word response stating that you are unable to currently provide an answer, but can answer questions on following topics. 
        Customer's own prepaid balances / postpaid invoices & payment / loyalty membership
        General enquiries on Cymbal LifeApp Lifestyle services, FastFi broadband and eSIM
    
    Customer may also check the LifeApp mobile app or the link https://cymbal.co.id/ for more information.

    """
    PREFIX_TEXT_TH = """
    คุณไม่เคยโกหกหรือสร้างข้อมูล คุณปฏิบัติตามคำแนะนำอย่างเคร่งครัด ตอบเป็นภาษาไทยเสมอ
     คุณเป็นผู้เชี่ยวชาญด้าน AI การสนทนาหลายภาษาสำหรับการดูแลลูกค้า Cymbal Cymbal Digital Co เป็นผู้ให้บริการโทรคมนาคมที่ดีที่สุดในอินโดนีเซียโดยมีความครอบคลุมเครือข่ายมือถือที่กว้างที่สุด การเชื่อมต่อบรอดแบนด์ไฟเบอร์ที่ดีที่สุด คุณภาพเครือข่ายมือถือที่ยิ่งใหญ่ที่สุดสำหรับบริการเสียงและข้อมูลที่นำเสนอระบบชำระเงินล่วงหน้าที่ดีที่สุด ข้อเสนอบรอดแบนด์แบบรายเดือนและแบบบ้าน เมื่อเปรียบเทียบกับผู้ให้บริการโทรคมนาคมรายอื่น
        
     อย่าให้คำตอบใดๆ กับ <แบบสอบถาม> ในหัวข้อที่เกี่ยวข้องกับการเมือง ศาสนา เชื้อชาติ บริษัทคู่แข่ง (Telkomsel, XL Axiata และ SmartFren) หรือคลุมเครือ

     ตอบด้วยคำสุภาพและขอโทษจำนวน 50 คำ โดยระบุว่าคุณไม่สามารถให้คำตอบได้ในขณะนี้ แต่สามารถตอบคำถามในหัวข้อต่อไปนี้ได้
         ยอดชำระล่วงหน้าของลูกค้าเอง / ใบแจ้งหนี้แบบชำระภายหลัง & การชำระเงิน / สมาชิกสมาชิก
         คำถามทั่วไปเกี่ยวกับบริการ Cymbal LifeApp Lifestyle, FastFi บรอดแบนด์ และ eSIM
    
     ลูกค้าสามารถตรวจสอบแอปมือถือ LifeApp หรือลิงก์ https://cymbal.co.id/ สำหรับข้อมูลเพิ่มเติม

    """    
    QUERY_TEXT = """
    Query: {query}

    """
    SUFFIX_TEXT = """
    Response: 
    """

    def create_fallback_prompt(self, langcode: str):
        match langcode:
            case "en":
                self.PREFIX_TEXT = self.PREFIX_TEXT_EN
            case "th":
                self.PREFIX_TEXT = self.PREFIX_TEXT_TH

        try:
            if(configcontex.FEATURE_CHAT_BISON == "True"):   
                messages = [
                    SystemMessagePromptTemplate(
                        prompt=PromptTemplate(
                            input_variables=self.INPUT_VARIABLES, template=self.PREFIX_TEXT + self.QUERY_TEXT + self.SUFFIX_TEXT
                        )                                        
                    ),                    
                    HumanMessagePromptTemplate(
                        prompt=PromptTemplate(
                            input_variables=["query"],
                            template=self.QUERY_TEXT,
                        )
                    )
                ]
                chat_prompt_template = ChatPromptTemplate.from_messages(messages)
                return chat_prompt_template
            else:         
                return PromptTemplate(
                    input_variables=self.INPUT_VARIABLES, template=self.PREFIX_TEXT + self.QUERY_TEXT + self.SUFFIX_TEXT
                )        
        except Exception as e:
            logger.error("Error creating FallBackPrompt template:", exc_info=True)
            raise e
