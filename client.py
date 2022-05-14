import sys
import threading
import Pyro4

# O daemon está executando em seu próprio encadeamento, para poder lidar com o servidor
# mensagens de retorno de chamada enquanto o thread principal está processando a entrada do usuário.

class Chatter(object):
    def __init__(self):
        self.chatbox = Pyro4.core.Proxy('PYRONAME:example.chatbox.server')
        self.abortar = 0

    @Pyro4.expose
    @Pyro4.oneway
    def message(self, apelido, msg):
        if apelido != self.apelido:
            print('[{0}] {1}'.format(apelido, msg))

    def start(self):
        apelidos = self.chatbox.getApelidos()
        if apelidos:
            print('Pessoas que estão no servidor agora: %s' % (', '.join(apelidos)))

        canais = sorted(self.chatbox.getCanais())
        if canais:
            print('Canais existentes: %s' % (', '.join(canais)))
            self.canal = input('Escolha um canal ou crie outro: ').strip()
        else:
            print('O servidor não tem canais ativos.')
            self.canal = input('Informe o nome do canal: ').strip()

        self.apelido = input('Digite seu apelido: ').strip()
        pessoa = self.chatbox.entrar(self.canal, self.apelido, self)
        print('%s entrou no canal %s' % (self.apelido,self.canal))
        print('Pessoas neste canal: %s' % (', '.join(pessoa)))
        print('Pronto para digitar! Para sair digite: /quit')
        try:
            try:
                while not self.abortar:
                    entrada = input('> ').strip()
                    if entrada == '/quit':
                        break

                    if entrada:
                        self.chatbox.publish(self.canal, self.apelido, entrada)
            except EOFError:
                pass
        finally:
            self.chatbox.sair(self.canal, self.apelido)
            self.abortar = 1
            self._pyroDaemon.shutdown()


class DaemonThread(threading.Thread):
    def __init__(self, chatter):
        threading.Thread.__init__(self)
        self.chatter = chatter
        self.setDaemon(True)

    def run(self):
        with Pyro4.core.Daemon() as daemon:
            daemon.register(self.chatter)
            daemon.requestLoop(lambda: not self.chatter.abortar)


chatter = Chatter()
daemonthread = DaemonThread(chatter)
daemonthread.start()
chatter.start()
print('Conexão encerrada.')
