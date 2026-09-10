import { apiClient } from "@/lib/api-client"
import * as mockGen from "@/mocks/generators"
import { getDocumentById, mockDocumentSummaries } from "@/mocks/documents"
import type {
  Citation,
  CompareResult,
  DocumentDetail,
  DocumentSummary,
  EvalRun,
  PipelineConfig,
  RetrievalResult,
  SummarizationStrategy,
  SummaryResponse,
} from "@/lib/types"
import type{Dispatch, SetStateAction} from "react"

/**
 * The API seam.
 *
 * Every page calls the functions below, never axios or mock data directly.
 * Today `USE_MOCKS` is true and everything resolves from `src/mocks/`; once
 * the FastAPI endpoints from IMPLEMENTATION_PLAN.md exist, flip a function
 * to its `apiClient` branch (or set VITE_USE_MOCKS=false) and the page that
 * calls it doesn't change.
 */
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS !== "false"

/** Simulated network latency so loading states are visible with mocks on. */
function mockDelay<T>(value: T, ms = 300 + Math.random() * 400): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms))
}

export const documentsApi = {
  list(): Promise<DocumentSummary[]> {
    //if (USE_MOCKS) return mockDelay(mockDocumentSummaries)
    return apiClient.get("/documents").then((res) => res.data)
  },

  get(documentId: string): Promise<DocumentDetail> {
    // if (USE_MOCKS) {
    //   const doc = getDocumentById(documentId)
    //   if (!doc) return Promise.reject(new Error(`Unknown document: ${documentId}`))
    //   return mockDelay(doc)
    // }
    return apiClient.get(`/documents/${documentId}`).then((res) => res.data)
  },
}

export const queryApi = {
  summarize(
    documentId: string,
    query: string,
    strategy: SummarizationStrategy = "naive",
  ): Promise<SummaryResponse> {
    // if (USE_MOCKS) {
    //   return mockDelay(mockGen.summarize(documentId, query, strategy), 600 + Math.random() * 900)
    // }
    return apiClient
      .post("/summarize", { documentId, query, strategy })
      .then((res) => res.data)
  },

  async summarizeWithStream(
  documentId: string,
  query: string,
  strategy: SummarizationStrategy = "naive",
  setAnswer: Dispatch<SetStateAction<string>>,
  setCitations: Dispatch<SetStateAction<Citation[] | undefined>>,
  setLatency: Dispatch<SetStateAction<number>>,
  setStrategy: Dispatch<SetStateAction<SummarizationStrategy>>,
  ){

    const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

    // axios dont support streaming event
    const res = await fetch(`${baseURL}/summarize/stream`, {method:"POST", headers: {"Content-Type" : "application/json"}, body: JSON.stringify({ documentId, query, strategy }),})
    
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    
    let buffer = "";
    
    while(true){
      const {value, done} = await reader.read();
      if(done){
        console.log(value)
        break;
      }
      

      buffer += decoder.decode(value, {stream: true});
      const frames = buffer.split("\n\n")
     
      buffer = frames.pop() ?? "";
     
      for(const frame of frames){
        
        if(!frame.startsWith("data: ")){
          continue;
        }

        const obj = JSON.parse(frame.slice(6));
       

        if(obj.type === "token"){
          setAnswer(prev=>prev+obj.text)
        }
        else if (obj.type === "done") {
          console.log("Done",obj)
          setCitations(obj.citations)
          setLatency(obj.latencyMs)
          setStrategy(obj.strategy)
        }
      }
      
    
    }


  },

  retrieve(documentId: string, query: string): Promise<RetrievalResult> {
    if (USE_MOCKS) return mockDelay(mockGen.retrieve(documentId, query))
    return apiClient.post("/query", { documentId, query }).then((res) => res.data)
  },
}

export const evalApi = {
  getLatestRun(): Promise<EvalRun> {
    if (USE_MOCKS) return mockDelay(mockGen.generateEvalRun())
    return apiClient.get("/eval/latest").then((res) => res.data)
  },
}

export const compareApi = {
  listPresets(): Promise<PipelineConfig[]> {
    if (USE_MOCKS) return mockDelay(mockGen.pipelinePresets)
    return apiClient.get("/compare/configs").then((res) => res.data)
  },

  run(documentId: string, query: string, configs: PipelineConfig[]): Promise<CompareResult[]> {
    if (USE_MOCKS) {
      return mockDelay(mockGen.compareConfigs(documentId, query, configs), 800 + Math.random() * 1200)
    }
    return apiClient
      .post("/compare", { documentId, query, configIds: configs.map((c) => c.id) })
      .then((res) => res.data)
  },
}
