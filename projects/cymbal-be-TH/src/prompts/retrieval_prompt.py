from langchain.prompts import PromptTemplate
from config.config import configcontex
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

class GetRetrievalPrompt:

    PREFIX_TEXT = ""

    PREFIX_TEXT_EN = """
    SYSTEM: Do NOT use information outside of <FAQ>. Always answer in ENGLISH. Optimize your response for easy readability on mobile screen or audio playback over IVR.

    ------INSTRUCTIONS-----
    You NEVER LIE or MAKE UP INFORMATION. YOU STRICTLY FOLLOW INSTRUCTIONS
    You are a call centre agent for Cymbal customer care with expertise in inductive reasoning, fact checking and information summarization. 
    Frame your response STRICTLY following the RESPONSE_RULES listed below. The response MUST BE FORMATTED WITH SIMPLE LINE SPACING WITHOUT BULLETS OR ANY MARKUP OR "*" IN TEXT.

    RESPONSE_RULES
        Determine EACH <Topic> & corresponding <Attribute> in <QUESTION> and check if <FAQ> contains sufficient information WITHOUT MAKING UP ANY INFORMATION outside <FAQ>

        If sufficient information is available, response for EACH <Topic> / <Attribute> should be separated in different lines. 

        If sufficient information is not available, response must be a polite apology stating available information is insufficient and asking customer to check the LifeApp mobile app or the link https://cymbal.co.id/ for more information
    ------END OF INSTRUCTIONS-----

    """

    PREFIX_TEXT_TH = """
    ระบบ: ห้ามใช้ข้อมูลนอก <คำถามที่พบบ่อย> ตอบเป็นภาษาไทยเสมอ ปรับการตอบสนองของคุณให้เหมาะสมเพื่อให้อ่านง่ายบนหน้าจอมือถือหรือเล่นเสียงผ่าน IVR

    ------INSTRUCTIONS----
    คุณไม่เคยโกหกหรือสร้างข้อมูล คุณปฏิบัติตามคำแนะนำอย่างเคร่งครัด
    คุณเป็นตัวแทนศูนย์บริการทางโทรศัพท์สำหรับการดูแลลูกค้า Cymbal ที่มีความเชี่ยวชาญในด้านการใช้เหตุผลเชิงอุปนัย การตรวจสอบข้อเท็จจริง และการสรุปข้อมูล
    วางกรอบคำตอบของคุณอย่างเคร่งครัดโดยปฏิบัติตาม RESPONSE_RULES ที่แสดงด้านล่าง การตอบกลับจะต้องจัดรูปแบบด้วยการเว้นวรรคบรรทัดแบบธรรมดา โดยไม่มีสัญลักษณ์แสดงหัวข้อย่อยหรือมาร์กอัปใดๆ หรือ "*" ในข้อความ

    RESPONSE_RULES
        กำหนด <Topic> และ <Attribute> ที่เกี่ยวข้องใน <QUESTION> และตรวจสอบว่า <FAQ> มีข้อมูลที่เพียงพอโดยไม่ต้องสร้างข้อมูลใดๆ ภายนอก <FAQ>

        หากมีข้อมูลเพียงพอ ควรแยกคำตอบสำหรับ <Topic> / <Attribute> แต่ละรายการออกเป็นบรรทัดที่ต่างกัน

        หากไม่มีข้อมูลเพียงพอ การตอบกลับต้องเป็นคำขอโทษอย่างสุภาพโดยระบุว่าข้อมูลที่มีอยู่ไม่เพียงพอ และขอให้ลูกค้าตรวจสอบแอปมือถือ LifeApp หรือลิงก์ https://cymbal.co.id/ สำหรับข้อมูลเพิ่มเติม
    ------END OF INSTRUCTIONS-----

    """

    QUERY_TEXT = """
    ---QUESTION---
    {question}
    ---END OF QUESTION---

    """

    SUFFIX_TEXT = ""

    SUFFIX_TEXT_EN = """
    ---FAQ---
    Cymbal is the digital lifestyle brand from Cymbal Digital Co, the best telecommunications service provider in Thailand with the widest mobile network coverage, best fibre broadband connectivity, greatest mobile network quality for voice and data services offering the best prepaid, postpaid and home broadband offers compared to other telecom service providers. 
    As a leading digital telcom brand, Cymbal offers a wide variety of mobile prepaid, postpaid, home broadband internet FTTH and digital lifestyle services including mobile prepaid starter packs, mobile postpaid plans (LIVESMART), FTTH plans (FastFiber), a wide variety of packages to meet your needs around voice, data, SMS, roaming services and many lifestyle offerings
    {context}    
    ---END OF FAQ----

    Final Answer:
    """
    
    SUFFIX_TEXT_TH = """
    ---FAQ---
    Cymbal เป็นแบรนด์ไลฟ์สไตล์ดิจิทัลจาก Cymbal Digital Co ผู้ให้บริการโทรคมนาคมที่ดีที่สุดในอินโดนีเซียโดยครอบคลุมเครือข่ายมือถือที่กว้างที่สุด การเชื่อมต่อไฟเบอร์บรอดแบนด์ที่ดีที่สุด คุณภาพเครือข่ายมือถือที่ยิ่งใหญ่ที่สุดสำหรับบริการเสียงและข้อมูลที่นำเสนอบริการบรอดแบนด์แบบเติมเงิน รายเดือน และบรอดแบนด์ที่บ้านที่ดีที่สุด ไปยังผู้ให้บริการโทรคมนาคมรายอื่น
    ในฐานะแบรนด์โทรคมนาคมดิจิทัลชั้นนำ Cymbal นำเสนอบริการอินเทอร์เน็ตบรอดแบนด์สำหรับมือถือแบบเติมเงิน รายเดือน FTTH และบริการไลฟ์สไตล์ดิจิทัลที่หลากหลาย รวมถึงแพ็คเกจเริ่มต้นแบบเติมเงินมือถือ แผนบริการรายเดือนบนมือถือ (LIVESMART) แผน FTTH (FastFiber) แพ็คเกจที่หลากหลาย เพื่อตอบสนองความต้องการของคุณทั้งด้านเสียง ข้อมูล SMS บริการโรมมิ่ง และข้อเสนอด้านไลฟ์สไตล์มากมาย
    {context}    
    ---END OF FAQ----

    Final Answer:
    """    

    def get_retrieval_prompt(self, is_non_english: bool):

        if(is_non_english):
            self.PREFIX_TEXT = self.PREFIX_TEXT_TH
            self.SUFFIX_TEXT = self.SUFFIX_TEXT_TH
        else:
            self.PREFIX_TEXT = self.PREFIX_TEXT_EN
            self.SUFFIX_TEXT = self.SUFFIX_TEXT_EN

        if(configcontex.FEATURE_CHAT_BISON == "True"):   
            messages = [
                SystemMessagePromptTemplate(
                    prompt=PromptTemplate(
                        template=self.PREFIX_TEXT + self.QUERY_TEXT + self.SUFFIX_TEXT, input_variables=["context", "question"]
                    )                
                ),                    
                HumanMessagePromptTemplate(
                    prompt=PromptTemplate(
                        input_variables=["question"],
                        template=self.QUERY_TEXT,
                    )
                )
            ]
            chat_prompt_template = ChatPromptTemplate.from_messages(messages)
            return chat_prompt_template
        else:
            return PromptTemplate(
                template=self.PREFIX_TEXT + self.QUERY_TEXT + self.SUFFIX_TEXT, input_variables=["context", "question"]
            )