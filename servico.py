import socket as s
import time as t
import logging as l
import threading as th
import hashlib as h
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
        self.__CHAVE_SECRETA = "secretsecret"
        
        self.__clientes = []        

        self.__server_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.__server_socket.bind(self.__ENDERECO_IP)
        self.__server_socket.listen()
        #self.__server_socket.settimeout(60)
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


    def iniciar_servidor(self):
        inicializar = ''
        iniciar_server = False
        while inicializar == '':
            os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            inicializar = input("Deseja inicializar o servidor [S/N] ? ").lower().strip()
            match inicializar:
                case 's':
                    iniciar_server = True
                    self.logger.info("Servidor foi inicializado!")
                case 'sim':
                    iniciar_server = True
                    self.logger.info("Servidor foi inicializado!")
                case 'n':
                    iniciar_server = False
                    self.logger.info("Servidor não foi inicializado!")
                case 'não':
                    iniciar_server = False
                    self.logger.info("Servidor não foi inicializado!")
                case _:
                    print('A escolha precisa estar nas opções acima!')
                    self.logger.warning("Resposta para o servidor não foi aceita!")
                    t.sleep(2)
                    inicializar = ''
        return iniciar_server


    def opcoes_servidor(self, cliente_socket:s.socket, endereco:tuple):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print(f"{len(self.__clientes)} cliente(s) conectado(s)...")
        
        opcao = 0
        cliente_opcao = self.mensagem_recebimento(cliente_socket, endereco).split("-")
        
        if cliente_opcao[0] == 'OPTION':
            opcao = int(cliente_opcao[1])
            
        match opcao:
            case 1:
                self.enviar_arquivo(cliente_socket, endereco)
                self.opcoes_servidor(cliente_socket, endereco)
            case 2:
                self.chat(cliente_socket, endereco)
                self.opcoes_servidor(cliente_socket, endereco)
            case 3:
                resposta = self.mensagem_recebimento(cliente_socket, endereco).split("-")
                if resposta[0] == "OK":
                    self.logger.warning(f"Cliente desconectado: {endereco}")
                    self.__clientes.remove(cliente_socket)
                    self.mensagem_envio(cliente_socket, endereco, 'OK-8-Desconectado')
                    
                    os.system('cls' if os.name == 'nt' else 'clear')
                    self.titulo()
                    print(f"{len(self.__clientes)} cliente(s) conectado(s)...")


    def run(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        iniciar_server = self.iniciar_servidor()
        os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print('Esperando resposta')

        while iniciar_server:
            cliente_socket, endereco = self.__server_socket.accept()
            self.__clientes.append(cliente_socket)
            
            thread = th.Thread(target=self.opcoes_servidor, args=(cliente_socket, endereco), daemon=True)
            thread.start()
        

if __name__ == "__main__":
    service = Servico()
    service.run()