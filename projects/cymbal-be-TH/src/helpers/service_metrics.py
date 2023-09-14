class ServiceMetrics:
    def __init__(self):
        self.servicemetrics = {"FlowType":"", "MetricsLangDetect":"", "MetricsLangTranslate":"", "MetricsVertexTextRequest":"", "MetricsVertexTextResponse":"", "MetricsVertexChatRequest":"", "MetricsVertexChatResponse":""}

    def setFlowType(self, flowtype: str):
        self.servicemetrics['FlowType'] = flowtype
        
    def setMetrics(self, metric: str, value: int):
        self.servicemetrics[metric] = self.servicemetrics[metric]+"-"+f'{value}'

    def getServiceMetrics(self):
        return self.servicemetrics

    def getServiceMetricsSummary(self):        
        summary = {"FlowType":"", "Metrics":""}
        separator = ""
        for key in self.servicemetrics:
            if(key == "FlowType"):
                summary["FlowType"] = self.servicemetrics[key]
            else:
                summary["Metrics"] = summary["Metrics"]+separator+key+self.servicemetrics[key]
                separator = ","
        return summary     