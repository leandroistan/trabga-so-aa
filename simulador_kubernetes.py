import threading
import queue
import time
import random

# Classe POD - As tarefas a serem executadas
class POD:
    def __init__(self, pod_id, cpu_req, ram_req, disco_req, tempo_execucao):
        self.pod_id = pod_id
        self.cpu_req = cpu_req
        self.ram_req = ram_req
        self.disco_req = disco_req
        self.tempo_execucao = tempo_execucao

# Classe WORKER - É o operário, vai atuar como o consumidor
class Worker(threading.Thread):
    def __init__(self, worker_id, cpu_max, ram_max, disco_max):
        super().__init__()
        self.daemon = True 
        self.worker_id = worker_id
        
        self.cpu_max = cpu_max
        self.ram_max = ram_max
        self.disco_max = disco_max
        
        self.cpu_livre = cpu_max
        self.ram_livre = ram_max
        self.disco_livre = disco_max
        
        self.fila_pods = queue.Queue()
        self.pods_processados = 0 
        self.tempo_ocioso = 0.0
        self.master = None

    def run(self):
        while True:

            # Calcula o tempo que o Worker ficou ocioso esperando um POD chegar na fila
            inicio_espera = time.time()
            pod_atual = self.fila_pods.get()
            fim_espera = time.time()
            self.tempo_ocioso += (fim_espera - inicio_espera)

            # Antes, subtraia os recursos aqui, mas passei a reservar no Master
            print(f"[WORKER {self.worker_id}] Iniciando {pod_atual.pod_id}... Recursos Livres (Reservados): CPU={self.cpu_livre}, RAM={self.ram_livre}, Disco={self.disco_livre}")
            
            time.sleep(pod_atual.tempo_execucao)
            
            # Aplicação terminou, devolve os recursos usando o Mutex do master
            with self.master.lock:
                self.cpu_livre += pod_atual.cpu_req
                self.ram_livre += pod_atual.ram_req
                self.disco_livre += pod_atual.disco_req
                self.pods_processados += 1 
            
            print(f"[WORKER {self.worker_id}] Finalizou {pod_atual.pod_id}! Recursos devolvidos.")

            self.master.revisar_pendentes()
            
            self.fila_pods.task_done()

# Classe MASTER - O 'escanlonador' e também produtor
class Master:
    def __init__(self, lista_workers):
        self.workers = lista_workers
        self.fila_pendentes = []
        self.lock = threading.Lock()

    def alocar_pod(self, pod):
        with self.lock:
            if not self._processar_alocacao(pod):
                print(f"[MASTER] POD {pod.pod_id} adicionado à fila de pendentes. Total pendentes: {len(self.fila_pendentes)}")
                self.fila_pendentes.append(pod)


    def _processar_alocacao(self, pod):    
        melhor_worker = None
        menor_espaco_sobrante = float('inf')

        # O algoritmo de escanlonamento escolhido foi o Best Fit
        for worker in self.workers:
            # Verifica se o Worker tem recursos suficientes para receber o POD
            if (worker.cpu_livre >= pod.cpu_req and 
                worker.ram_livre >= pod.ram_req and 
                worker.disco_livre >= pod.disco_req):
                
                # Calcula quanto espaço ficaria sobrando 
                espaco_sobrante = (worker.cpu_livre - pod.cpu_req) + \
                                  (worker.ram_livre - pod.ram_req) + \
                                  (worker.disco_livre - pod.disco_req)
                
                # Busca sempre o que deixa o menor espaço sobrando
                if espaco_sobrante < menor_espaco_sobrante:
                    menor_espaco_sobrante = espaco_sobrante
                    melhor_worker = worker

        if melhor_worker:

            # Master já reserva os recursos imediatamente
            melhor_worker.cpu_livre -= pod.cpu_req
            melhor_worker.ram_livre -= pod.ram_req
            melhor_worker.disco_livre -= pod.disco_req

            print(f"[MASTER] POD {pod.pod_id} escalonado para Worker {melhor_worker.worker_id}")
            melhor_worker.fila_pods.put(pod)
            return True
        
        return False
    
    def revisar_pendentes(self):
        with self.lock:
            if not self.fila_pendentes:
                return
            
            print(f"[MASTER] Revisando fila de pendentes. Total: {len(self.fila_pendentes)}")
            pendentes_restantes = []

            for pod in self.fila_pendentes:
                if not self._processar_alocacao(pod):
                    pendentes_restantes.append(pod)

            self.fila_pendentes = pendentes_restantes

if __name__ == "__main__":
    print("*" * 50)
    print("Iniciando o Simulador Kubernetes")

    # Instanciei 3 perfis de Workers para simular diferentes tipos de nós em um cluster Kubernetes
    # Equilibrado, com muita RAM e Disco (para bancos de dados), e com muita CPU (para processamento intenso)
    w1 = Worker(worker_id=1, cpu_max=4000, ram_max=16, disco_max=500) 
    w2 = Worker(worker_id=2, cpu_max=8000,  ram_max=32, disco_max=1000)
    w3 = Worker(worker_id=3, cpu_max=2000, ram_max=8,  disco_max=250) 

    lista_workers = [w1, w2, w3]
    master = Master(lista_workers)

    # Conecta o master aos workers para que eles possam acessar o lock e revisar a fila de pendentes
    # Liga as threads
    for w in lista_workers:
        w.master = master
        w.start()

    # Gerar a carga de trabalho: 20 PODs com requisitos aleatórios
    tipos_pods = ["Frontend", "Backend", "Database", "Cache"]
    
    print("\nGerando e Alocando PODs")
    for i in range(1, 21):
        tipo = random.choice(tipos_pods)
        pod_id = f"POD_{i}_{tipo}"
        
        # Gera requisitos aleatórios para cada POD
        req_cpu = random.randint(200, 1500)
        req_ram = random.randint(1, 6)
        req_disco = random.randint(10, 50)
        tempo_exec = random.randint(1, 3)

        novo_pod = POD(pod_id, req_cpu, req_ram, req_disco, tempo_exec)

        # Master tenta alocar o POD no melhor Worker disponível (Best Fit)
        master.alocar_pod(novo_pod)

        # Pausa de meio segundo apenas para conseguirmos ler o terminal com calma
        time.sleep(0.1) 

    print("\n[SISTEMA] Todos os PODs foram enviados para as filas. Aguardando processamento...\n")

    while True:
        tarefas_ativas = len(master.fila_pendentes)
        for w in lista_workers:
            tarefas_ativas += w.fila_pods.unfinished_tasks

        if tarefas_ativas == 0:
            break
        time.sleep(0.5)

    print("\nSimulação Concluída! Todos os PODs foram processados.")

    # Relatório estatístico para mostrar quantos PODs cada Worker processou e os recursos finais disponíveis em cada um
    print("\n" + "*"*60)
    print("RELATÓRIO ESTATÍSTICO DO CLUSTER KUBERNETES ")
    print("*"*60)
    
    total_pods_cluster = 0
    for w in lista_workers:
        print(f"WORKER {w.worker_id} (CPU: {w.cpu_max}m, RAM: {w.ram_max}GB, Disco: {w.disco_max}GB)")
        print(f" -> PODs Processados: {w.pods_processados}")
        print(f" -> Tempo Ocioso: {w.tempo_ocioso:.2f} segundos")
        print(f" -> Recursos Finais : CPU Livre: {w.cpu_livre} | RAM Livre: {w.ram_livre}GB | Disco Livre: {w.disco_livre}GB")
        print("-" * 60)
        total_pods_cluster += w.pods_processados
        
    print(f"TOTAL DE PODs PROCESSADOS NO CLUSTER: {total_pods_cluster}")
    print("*"*60 + "\n")