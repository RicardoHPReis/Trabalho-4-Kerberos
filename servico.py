import socket as s
import time as t
import datetime as d
import logging as l
import threading as th
import hashlib as h
import base64 as b64
import json as j
from Cryptodome.Cipher import AES
import Cryptodome.Random as r
import Crypto.Random.random as ri
import os

# Serviço
class Servico:
    def __init__(self):
        self.logger = l.getLogger(__name__)
        l.basicConfig(filename="./log/servico.log", encoding="utf-8", level=l.INFO, format="%(levelname)s - %(asctime)s: %(message)s")

        self.__NOME_DO_SERVER = ''
        self.__PORTA_DO_SERVER = 8000
        self.__TAM_BUFFER = 2048
        self.__ENDERECO_IP = (self.__NOME_DO_SERVER, self.__PORTA_DO_SERVER)
        self.__clientes = []        
        
        self.__servico = ""
        self.__chave = ""
        self.__tempo = 0
        self.__chave_sessao_servico = r.get_random_bytes(16).hex()
        self.__numero_aleatorio = ri.randint(1000,10000)

        self.__server_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.__server_socket.bind(self.__ENDERECO_IP)
        self.__server_socket.listen()
        self.__server_socket.settimeout(30)
        self.logger.info(f"Socket do servidor criado na porta: '{self.__PORTA_DO_SERVER}'")
        
    
    def __del__(self):
        self.logger.info(f"Socket finalizado!")
        for cliente in self.__clientes:
            self.cliente.close()
            
        self.__clientes.clear()
        self.__server_socket.close()
        os.system('cls' if os.name == 'nt' else 'clear')
        
    
    def titulo(self):
        print("--------------------")
        print("       SERVIÇO")
        print("--------------------\n")


    def selecionar_servico(self):
        servico_encontrado = False
        while not servico_encontrado:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            self.__servico = input("Digite seu serviço: ")
            self.__chave = h.sha256(input("Digite sua senha: ").encode()).hexdigest()
            
            pesquisa = self.pesquisar("./data/servidor_TGS.txt", self.__servico)
            
            if pesquisa == {}:
                print("Usuário não encontrado")
            else:
                if self.__chave == pesquisa['senha']:
                    print("Usuário autenticado")
                    self.__tempo = pesquisa['tempo']
                    servico_encontrado = True
                else:
                    print("Senha incorreta")
                    
            t.sleep(3)


    def fechar_conexao(self, cliente_socket : s.socket, endereco : tuple):
        resposta = self.mensagem_recebimento(cliente_socket, endereco).split("-")
        if resposta[0] == "OK":
            self.logger.warning(f"Cliente desconectado: {endereco}")
            self.__clientes.remove(cliente_socket)
            self.mensagem_envio(cliente_socket, endereco, 'OK-8-Desconectado')
            
            os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            print(f"{len(self.__clientes)} cliente(s) conectado(s)...")


    def mensagem_envio(self, cliente_socket : s.socket, endereco : tuple, mensagem : str):
        try:
            cliente_socket.send(mensagem.encode())
            self.logger.info(f"Destinatário: {endereco} - Enviado:  '{mensagem}'")
        except:
            self.logger.error(f"Cliente removido:  {endereco}")
            self.__clientes.remove(cliente_socket)


    def mensagem_recebimento(self, cliente_socket : s.socket, endereco : tuple):
        try:
            mensagem = cliente_socket.recv(self.__TAM_BUFFER).decode('utf-8')
            self.logger.info(f"Remetente: {endereco} - Recebido: '{mensagem}'")
            return mensagem
        except:
            self.logger.error(f"Cliente removido:  {endereco}")
            self.__clientes.remove(cliente_socket)

    
    def ler_arquivo(self, caminho:str) -> list:
        cabecalho = []
        lista = []
        with open(caminho, 'r') as arquivo:
            for n, linha in enumerate(arquivo):
                registro = linha.replace("\n","").split(' ')
                if n == 0:
                    cabecalho = registro
                    continue
                lista.append(registro)
        
        dicionario = []
        for user in lista:
            dicionario.append(dict(zip(cabecalho, user)))
        
        return dicionario


    def pesquisar(self, caminho:str, texto:str) -> dict:
        lista = self.ler_arquivo(caminho)
        
        for dic in lista:
            for key, value in dic.items():
                if value == texto:
                    return dic
        return {}


    def escrever_arquivo(self, caminho:str, dados:dict) -> None:   
        with open(os.path.join(caminho), "a") as arquivo:
            arquivo.write(' '.join([''.join(i) for i in dados.values()]))
            arquivo.write('\n')
        arquivo.close()
    
    
    def criptografar(self, payload:str, chave:str) -> str:
        pad = lambda s: s + (AES.block_size - len(s) % AES.block_size) * chr(AES.block_size - len(s) % AES.block_size)
        
        chave = bytes.fromhex(chave)
        payload = b64.b64encode(pad(payload).encode('utf8'))
        iv = r.get_random_bytes(AES.block_size)
        cifra = AES.new(chave, AES.MODE_CFB, iv)
        texto_cripto = b64.b64encode(iv + cifra.encrypt(payload))
        
        iv_2 = r.new().read(AES.block_size)
        aes = AES.new(chave, AES.MODE_CFB, iv_2)
        criptografado = b64.b64encode(iv_2 + aes.encrypt(texto_cripto))
        return criptografado.decode('utf8')


    def descriptografar(self, criptografado:str, chave:str) -> str:
        unpad = lambda s: s[:-ord(s[-1:])]
        
        criptografado = criptografado.encode()
        chave = bytes.fromhex(chave)
        criptografado = b64.b64decode(criptografado)
        iv_2 = criptografado[:AES.block_size]
        aes = AES.new(chave, AES.MODE_CFB, iv_2)
        payload_cripto = b64.b64decode(aes.decrypt(criptografado[AES.block_size:]))
        
        iv = payload_cripto[:AES.block_size]
        cifra = AES.new(chave, AES.MODE_CFB, iv)
        payload = unpad(b64.b64decode(cifra.decrypt(payload_cripto[AES.block_size:])).decode('utf8'))
        return payload


    def verificar(self, cliente_socket:s.socket, endereco:tuple):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print(f"{len(self.__clientes)} cliente(s) conectado(s)...")
        
        recebido = self.mensagem_recebimento(cliente_socket, endereco)
        mensagem = j.loads(recebido.replace("'", "\""))
        
        dados_ticket = self.descriptografar(mensagem['ticket'], self.__chave)
        dados_ticket = j.loads(dados_ticket.replace("'", "\""))
        self.__chave_randomica_TGS = dados_ticket['chave_sessao_servico']
            
        dados_auth = self.descriptografar(mensagem['dados'], self.__chave_randomica_TGS)
        dados_auth = j.loads(dados_auth.replace("'", "\""))
        self.__numero_aleatorio = dados_auth["numero_aleatorio"]
        
        if dados_auth['usuario'] == dados_ticket['usuario']:
            #auth_timestamp = d.datetime.strptime(dados_auth['horario'], "%Y-%m-%d %H:%M:%S.%f")
            #tgt_timestamp = d.datetime.strptime(dados_ticket['horario'], "%Y-%m-%d %H:%M:%S.%f")
            #elapsed_time_in_hours = divmod((auth_timestamp - tgt_timestamp).seconds, 3600)[0]
            
            status = {"status": "OK", 
                      "numero_aleatorio": self.__numero_aleatorio}

            resposta = self.criptografar(str(status), self.__chave_randomica_TGS)
            self.mensagem_envio(cliente_socket, endereco, str(resposta))
                
        self.fechar_conexao(cliente_socket, endereco)


    def run(self):
        self.selecionar_servico()
        os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print('Esperando resposta')

        while True:
            cliente_socket, endereco = self.__server_socket.accept()
            self.__clientes.append(cliente_socket)
            thread = th.Thread(target=self.verificar, args=(cliente_socket, endereco), daemon=True)
            thread.start()
        

if __name__ == "__main__":
    service = Servico()
    service.run()