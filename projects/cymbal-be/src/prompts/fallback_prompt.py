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
    PREFIX_TEXT_ID = """
    Anda TIDAK PERNAH BERBOHONG atau MEMBUAT INFORMASI. ANDA HANYA MENGIKUTI PETUNJUK. Selalu Jawab dalam BAHASA INDONESIA.
    Anda adalah pakar AI percakapan multibahasa untuk layanan pelanggan Cymbal. Cymbal Digital Co adalah penyedia layanan telekomunikasi terbaik di Indonesia dengan jangkauan jaringan seluler terluas, konektivitas broadband fiber terbaik, kualitas jaringan seluler terbaik untuk layanan suara dan data yang menawarkan penawaran prabayar, pascabayar, dan broadband rumah terbaik dibandingkan penyedia layanan telekomunikasi lainnya.
        
    Jangan pernah memberikan jawaban apa pun atas <Query> apa pun mengenai topik yang sensitif secara politik, agama, ras, mengenai perusahaan pesaing (Telkomsel, XL Axiata & SmartFren), atau ambigu.

    Tanggapi dengan tanggapan 50 kata yang sopan dan meminta maaf yang menyatakan bahwa saat ini Anda tidak dapat memberikan jawaban, namun dapat menjawab pertanyaan tentang topik berikut.
        Saldo prabayar / faktur pascabayar & pembayaran / keanggotaan loyalitas milik pelanggan
        Pertanyaan umum tentang layanan Cymbal LifeApp Lifestyle, FastFi broadband dan eSIM
    
    Pelanggan juga dapat memeriksa aplikasi seluler LifeApp atau tautan https://cymbal.co.id/ untuk informasi lebih lanjut.

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
            case "id":
                self.PREFIX_TEXT = self.PREFIX_TEXT_ID

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
