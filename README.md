# Trabalho GA - Sistemas Operacionais (Análise e Aplicação)
# Simulador de Escalonamento Kubernetes 

**Disciplina:** Análise e Aplicação de Sistemas Operacionais  
**Instituição:** UNISINOS - Universidade do Vale do Rio dos Sinos  

Este projeto é um simulador desenvolvido em **Python** que replica o comportamento do nó Master (Job Scheduler) e dos nós Workers de um cluster Kubernetes. O objetivo principal é demonstrar na prática os conceitos avançados de Sistemas Operacionais, incluindo **concorrência, multithreading, sincronização (Mutex)** e o paradigma **Produtor-Consumidor**.

---

## Arquitetura do Sistema

A arquitetura foi desenhada baseada no paradigma **Produtor-Consumidor**, dividida em três entidades principais:

### 1. PODs (As Tarefas)
Representam as aplicações a serem executadas. Diferente do escalonador padrão do Kubernetes (que analisa apenas CPU e Memória), neste simulador cada POD exige recursos baseados em **três métricas obrigatórias**:
* **CPU** (medida em *millicores*, onde 1000m = 1 vCPU)
* **Memória RAM** (em GB)
* **Espaço em Disco** (em GB)

### 2. Nodos Workers (Consumidores)
Os servidores físicos do cluster. Cada Worker foi implementado como uma **Thread independente** (`threading.Thread`), permitindo processamento simultâneo.
* Eles possuem filas exclusivas e seguras (`queue.Queue`).
* Simulam o tempo de execução da aplicação e, ao final, devolvem os recursos de CPU, RAM e Disco para a contabilidade global do cluster.
* Calculam o seu próprio **Tempo Ocioso** (*Idle Time*) enquanto aguardam novas tarefas.

### 3. Nodo Master (Produtor / Scheduler)
O cérebro do cluster. O Master avalia a fila de PODs e decide para qual Worker enviar a tarefa com base num **Algoritmo Best Fit (Melhor Encaixe)**.
* **Lógica Best Fit:** O Master simula matematicamente a alocação e escolhe o Worker que ficará com o *menor espaço sobrante*. Isso minimiza a fragmentação de recursos no cluster, preservando Workers maiores para cargas pesadas.
* **Reserva Imediata:** Para evitar sobrecarga rápida (ilusão de ótica do escalonador), o Master reserva os recursos imediatamente antes de enviar o POD.

---

## Sincronização e Recursos Utilizados

Para garantir a integridade dos dados num ambiente altamente concorrente, foram aplicadas as seguintes ferramentas:

* **Multithreading:** Uso intensivo da biblioteca nativa `threading` para paralelismo.
* **Filas Thread-Safe:** A comunicação entre o Master e os Workers ocorre via `queue.Queue`, que gere os seus próprios bloqueios internamente para evitar colisões.
* **MUTEX (Locks):** Implementação de `threading.Lock()` global no Master. Quando um Worker termina a sua tarefa, ele utiliza o Mutex para **"trancar a porta"** e devolver os recursos de forma segura, evitando Condições de Corrida (*Race Conditions*).
* **Pending Queue (Fila de Espera):** Quando o cluster atinge a capacidade máxima, os PODs não são descartados. Eles entram em estado de **Pending**  e aguardam. O aviso de libertação de recursos pelos Workers aciona o Master (sob proteção do Mutex) para realocar estes PODs pendentes de forma segura[cite: .

---

## Resultados e Estatísticas

No final da simulação, o sistema gera um **Relatório Estatístico** comprovando a eficiência do algoritmo:

1. **Eficiência do Best Fit:** O relatório de "Tempo Ocioso" prova que a carga foi distribuída de forma inteligente, priorizando o preenchimento ideal das máquinas e justificando o poder computacional dos Workers maiores.
2. **Ausência de *Memory Leaks*:** A contabilidade final demonstra que todos os *Millicores*, GB de RAM e de Disco retornaram exatamente aos seus 100% de capacidade original após as threads finalizarem, provando a gestão perfeita do ciclo de vida dos PODs (Alocação -> Consumo -> Libertação).
3. **Simulação Realista:** O comportamento do sistema ao esgotar recursos imita com exatidão o estado *Pending* do Kubernetes em produção.

---

## Como Executar o Projeto

O simulador é multiplataforma e não requer bibliotecas externas além da instalação padrão do Python 3.x.

**Passo 1: Clonar o repositório**
```bash
git clone [https://github.com/leandroistan/trabga-so-aa.git](https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git)
cd SEU_REPOSITORIO
