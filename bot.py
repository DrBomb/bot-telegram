from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from cachama_templates import new_cachama, old_cachama
import telebot, random, datetime, time

DEBUG = True
LAST_CALL_PERIOD = 1*3600
engine = create_engine("sqlite:///users.db",echo=True)
Session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer,nullable=False,primary_key=True)
    username = Column(String)
    cachamas = relationship("Cachama",backref="user",uselist=False)
class Cachama(Base):
    __tablename__ = 'cachama'
    id = Column(Integer,ForeignKey("user.id"),nullable=False,primary_key=True)
    total = Column(Integer,default=0)
    last_call= Column(DateTime)

Base.metadata.create_all(engine)

with open("token.txt") as f:
    token = f.read()
    bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start'])
def startMessage(message):
    bot.send_message(message.chat.id,"Soy el bot de laboratorio de prototipos")

@bot.message_handler(commands=['cachama','cachamas'])
def cachama(message):
    session = Session()
    if (message.chat.type == 'private' or message.chat.type == 'channel') and DEBUG == False:
        return
    user = session.query(User).filter(User.id == message.from_user.id).one_or_none()
    if user is None:
        user = User(id=message.from_user.id,username=message.from_user.username)
        session.add(user)
        cachama = Cachama(id=message.from_user.id,total=0,last_call=datetime.datetime.utcfromtimestamp(time.time()-(LAST_CALL_PERIOD+1)))
        session.add(cachama)
        session.flush()
    if user.username is None:
        user.username = message.from_user.username
        session.flush()
        print user.username, " agregado"
    delta = datetime.datetime.now() - user.cachamas.last_call
    if delta.seconds > LAST_CALL_PERIOD:
        new_cachamas = generate_new_cachamas()
        user.cachamas.total = user.cachamas.total+new_cachamas
        user.cachamas.last_call = datetime.datetime.now()
        response = random.choice(new_cachama).format(name=message.from_user.first_name,new=new_cachamas,total=user.cachamas.total)
        session.commit()
    else:
        response = random.choice(old_cachama).format(name=message.from_user.first_name,total=user.cachamas.total)
        session.commit()
        pass
    Session.remove()
    bot.send_message(message.chat.id,response)

@bot.message_handler(commands=['cachamaranking'])
def cachamaranking(message):
    session = Session()
    if ( message.chat.type == 'private' or message.chat.type == 'channel') and DEBUG == False:
        return
    ranking = session.query(Cachama).order_by(Cachama.total.desc())
    response = "El RANKING CACHAMA va hasta la fecha de hoy:"
    for x in range(len(response)):
        response += "#{}! {}\n".format(x+1,response[x])
    bot.send_message(message.chat.id,response)


def new_user(id_new):
    user = User(id=id_new)
    session.add(user)
    session.commit()

def generate_new_cachamas():
    return (10*random.randint(0,9))+random.randint(0,9)

if __name__ == "__main__":
    bot.polling()


