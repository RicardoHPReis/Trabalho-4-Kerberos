import socket as s
import time as t
import logging as l
import json as j
import hashlib as h
import base64 as b64
from Cryptodome.Cipher import AES
import Cryptodome.Random as r
import Crypto.Random.random as ri
import os


class Cliente:
    def __init__(self):
        self.logger = l.getLogger(__name__)
        l.basicConfig(filename="./log/cliente.log", encoding="utf-8", level=l.INFO, format="%(levelname)s - %(asctime)s: %(message)s")
        
        self.__NOME_DO_SERVER = '127.0.0.1'
        self.__porta_do_server = 0
        self.__endereco_IP = (self.__NOME_DO_SERVER, self.__porta_do_server)
        self.__TAM_BUFFER = 2048
        
        self.__usuario = ""
        self.__chave = ""
        self.__servico = ""
        self.__chave_randomico_AS = ""
        self.__chave_randomico_TGS = ""
        self.__TEMPO_SERVICO = 3600
        self.__tempo_autorizado = 0
        self.__ticket_as = ""
        self.__ticket_tgs = ""
        self.__numero_aleatorio = ri.randint(1000,10000)
        
        
    def titulo(self):
        print("--------------------")
        print("       CLIENTE")
        print("--------------------\n")


    def opcoes_cliente(self):
        #os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print("1) Conectar no Kerberos.")
        print("2) Conectar no Serviço.")
        print("3) Criar novo cliente.")
        print("4) Criar novo serviço.")
        print("5) Sair.\n")
        
        opcao = int(input("Escolha uma opção: "))
        match opcao:
            case 1:
                self.enviar_dados_AS()
                self.enviar_dados_TGS()
                self.enviar_dados_servico()
                self.opcoes_cliente()
            case 2:
                self.enviar_dados_servico()
                self.opcoes_cliente()
            case 3:
                self.criar_usuario()
                self.opcoes_cliente()
            case 4:
                self.criar_servico()
                self.opcoes_cliente()
            case 5:
                print("Saindo do sistema.")
                t.sleep(3)
                os.system('cls' if os.name == 'nt' else 'clear')
            case _:
                print('A escolha precisa estar nas opções acima!')
                t.sleep(2)
                self.opcoes_cliente()
                
    
    def conectar_servidor(self, porta:int):
        os.system('cls' if os.name == 'nt' else 'clear')

        self.__conexao_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.__conexao_socket.settimeout(30)
        self.__porta_do_server = porta
        self.__endereco_IP = (self.__NOME_DO_SERVER, self.__porta_do_server)
        self.__conexao_socket.connect(self.__endereco_IP)

        try:
            self.logger.info(f"Cliente conectado ao servidor: {self.__endereco_IP}")
        except TimeoutError:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            print("ERROR-5-Excedeu-se o tempo para comunicação entre o servidor e o cliente!")
        except Exception as e:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            print("ERROR-0-Erro não registrado!")
            print(e)


    def mensagem_envio(self, mensagem : str):
        try:
            self.__conexao_socket.send(mensagem.encode())
            self.logger.info(f"Destinatário: {self.__endereco_IP} - Enviado:  '{mensagem}'")
        except:
            self.logger.error(f"Removido do Servidor:  {self.__endereco_IP}")
            self.__conexao_socket.close()


    def mensagem_recebimento(self):
        try:
            mensagem = self.__conexao_socket.recv(self.__TAM_BUFFER).decode('utf-8')
            self.logger.info(f"Remetente: {self.__endereco_IP} - Recebido: '{mensagem}'")
            return mensagem
        except:
            self.logger.error(f"Removido do Servidor:  {self.__endereco_IP}")
            self.__conexao_socket.close()


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


    def fechar_conexao(self):
        self.mensagem_envio('OK-8-Desconectar servidor')
        resposta = self.mensagem_recebimento().split("-")
        
        if resposta[0] == "OK":
            self.logger.info(f"Deletando Socket:  {self.__endereco_IP}")
            self.__conexao_socket.close()
            return
        else:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.logger.error(f"Deletando Socket:  {self.__endereco_IP}")
            self.__conexao_socket.close()
            return
                

    def criar_usuario(self):
        usuario_novo = False
        while not usuario_novo:
            usuario = input("Digite o seu usuário: ")
            chave = input("Digite sua senha: ")
            chave_hash = h.sha256(chave.encode()).hexdigest()
            if self.pesquisar("./data/servidor_AS.txt", chave_hash) == {}:
                usuario_novo = True
        
        dict_cliente = {"usuario": usuario, "senha": chave}
        dict_AS = {"usuario": usuario, "senha": chave_hash}
        
        self.escrever_arquivo("./data/usuario.txt", dict_cliente)
        self.escrever_arquivo("./data/servidor_AS.txt", dict_AS)
    
    
    def criar_servico(self):
        servico_novo = False
        while not servico_novo:
            servico = input("Digite o nome do serviço: ")
            chave = input("Digite a senha do serviço: ")
            tempo = input("Digite o tempo de uso do serviço: ")
            chave_hash = h.sha256(chave.encode()).hexdigest()
            if self.pesquisar("./data/servidor_TGS.txt", chave_hash) == {}:
                servico_novo = True
        
        dict_cliente = {"servico": servico, "senha": chave, "tempo": tempo}
        dict_TGS = {"servico": servico, "senha": chave_hash, "tempo": tempo}
        
        self.escrever_arquivo("./data/servico.txt", dict_cliente)
        self.escrever_arquivo("./data/servidor_TGS.txt", dict_TGS)


    def enviar_dados_AS(self):
        self.conectar_servidor(6000)
        
        usuario_encontrado = False
        while not usuario_encontrado:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            self.__usuario = input("Digite o seu usuário: ")
            self.__chave = h.sha256(input("Digite sua senha: ").encode()).hexdigest()
            self.__servico = input("Digite seu serviço: ")
            
            dados_sensiveis = {"servico": self.__servico, 
                               "tempo_servico": self.__TEMPO_SERVICO, 
                               "numero_aleatorio": self.__numero_aleatorio}
            dados_criptografados = self.criptografar(str(dados_sensiveis), self.__chave)
            
            envio = {"usuario": self.__usuario, 
                     "dados": dados_criptografados}
            self.mensagem_envio(str(envio))

            resposta = self.mensagem_recebimento().split("-")
            if resposta[0] == "OK":
                print(resposta[2])
                t.sleep(3)
                usuario_encontrado = True
            else:
                print(resposta[2])
                t.sleep(3)
        
        resposta = self.mensagem_recebimento()
        resposta = j.loads(resposta.replace("'", "\""))
        autenticacao = self.descriptografar(resposta['auth'], self.__chave)
        autenticacao = j.loads(autenticacao.replace("'", "\""))
        
        self.__chave_randomico_AS = autenticacao['chave_sessao_tgs']
        self.__ticket_as = resposta['ticket']
        
        self.fechar_conexao()
        

    def enviar_dados_TGS(self):
        self.conectar_servidor(7000)
        
        self.__numero_aleatorio = ri.randint(1000, 10000)
        dados_sensiveis = {"usuario": self.__usuario, 
                           "servico": self.__servico, 
                           "tempo_servico": self.__TEMPO_SERVICO, 
                           "numero_aleatorio": self.__numero_aleatorio}
        dados_criptografados = self.criptografar(str(dados_sensiveis), self.__chave_randomico_AS)
        
        envio = {"dados": dados_criptografados, 
                 "ticket": self.__ticket_as}
        self.mensagem_envio(str(envio))
        
        resposta = self.mensagem_recebimento()
        resposta = j.loads(resposta.replace("'", "\""))
        
        tgs_ack = self.descriptografar(resposta['tgs_ack'], self.__chave_randomico_AS)
        tgs_ack = j.loads(tgs_ack.replace("'", "\""))

        self.__chave_randomico_TGS = tgs_ack['chave_sessao_servico']
        self.__tempo_autorizado = tgs_ack['tempo_servico']
        self.__ticket_tgs = resposta['ticket']
        
        self.fechar_conexao()
    
    
    def enviar_dados_servico(self):
        self.conectar_servidor(8000)
        
        self.__numero_aleatorio = ri.randint(1000, 10000)
        dados_sensiveis = {"usuario": self.__usuario, 
                           "servico": self.__servico, 
                           "tempo_servico": self.__tempo_autorizado, 
                           "numero_aleatorio": self.__numero_aleatorio}
        dados_criptografados = self.criptografar(str(dados_sensiveis), self.__chave_randomico_TGS)
        
        envio = {"dados": dados_criptografados, 
                 "ticket": self.__ticket_tgs}
        self.mensagem_envio(str(envio))
        
        recebimento = self.mensagem_recebimento()
        resposta = self.descriptografar(recebimento, self.__chave_randomico_TGS)
        resposta = j.loads(resposta.replace("'", "\""))
        print(resposta)
        
        self.fechar_conexao()


    def run(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.opcoes_cliente()
        

if __name__ == "__main__": 
    cliente = Cliente()
    cliente.run()