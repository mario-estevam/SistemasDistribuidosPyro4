import Pyro4

#Servidor de administrador do bate-papo.
# Responsável por logins, logouts, canais e apelidos, e a troca de mensagens.
@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class ChatBox(object):
    def __init__(self):
        # canais registrados
        self.canais = {}
        # Todos os apelidos registrados no servidor
        self.apelidos = []

    def getCanais(self):
        return list(self.canais.keys())

    def getApelidos(self):
        return self.apelidos

    def entrar(self, canal, apelido, callback):
        if not canal or not apelido:
            raise ValueError("Canal ou apelido inválido")
        if apelido in self.apelidos:
            raise ValueError('Este apelido já está em uso')
        if canal not in self.canais:
            print('Criando novo canal %s' % canal)
            self.canais[canal] = []

        self.canais[canal].append((apelido, callback))
        self.apelidos.append(apelido)
        print("%s entrou no canal %s" % (apelido, canal))

        #faz um publish para informar que uma pessa entrou
        self.publish(canal, 'SERVIDOR', '** ' + apelido + ' entrou **')
        return [apelido for (apelido, c) in self.canais[canal]]  # retorna todos os apelidos do canal

    def sair(self, canal, apelido):
        if canal not in self.canais:
            print('Canal desconhecido foi ignorado %s' % canal)
            return

        for (n, c) in self.canais[canal]:
            if n == apelido:
                self.canais[canal].remove((n, c))
                break

        #faz um publish para informar que uma pessoa saiu
        self.publish(canal, 'SERVIDOR', '** ' + apelido + ' saiu **')
        if len(self.canais[canal]) < 1:
            del self.canais[canal]
            print('Canal %s foi excluido' % canal)

        self.apelidos.remove(apelido)
        print("%s saiu %s" % (apelido, canal))

    def publish(self, canal, apelido, msg):
        if canal not in self.canais:
            print('Canal desconhecido ignorado %s' % canal)
            return

        for (n, c) in self.canais[canal][:]:  # usa uma copia da lista
            try:
                c.message(apelido, msg)  # chamada oneway
            except Pyro4.errors.ConnectionClosedError:
                # conexão caiu, remova o ouvinte se ele ainda estiver lá
                if (n, c) in self.canais[canal]:
                    self.canais[canal].remove((n, c))
                    print('O usuário %s estava sem conexão e foi removido do canal. %s' % (n, c))

Pyro4.Daemon.serveSimple({
    ChatBox: "example.chatbox.server"
})
