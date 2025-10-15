from flask import Flask, render_template, request, redirect, url_for, jsonify
from controller.controllerCarro import *
from flask import Flask, render_template, request, redirect, url_for, jsonify, session


#Para subir archivo tipo foto al servidor
import os
from werkzeug.utils import secure_filename 


#Declarando nombre de la aplicación e inicializando, crear la aplicación Flask
app = Flask(__name__)
application = app

msg  =''
tipo =''


#Creando mi decorador para el home, el cual retornara la Lista de Carros
@app.route('/', methods=['GET','POST'])
def inicio():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('public/layout.html', miData = listaCarros())

from flask import session
from conexionBD import connectionBD

app.secret_key = 'tu_clave_secreta'  # Necesario para usar sesiones

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conexion = connectionBD()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conexion.close()
        if user:
            session['usuario'] = username
            return redirect(url_for('inicio'))
        else:
            msg = 'Usuario o contraseña incorrectos'
    return render_template('public/login.html', msg=msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conexion = connectionBD()
        cursor = conexion.cursor()
        # Verifica si el usuario ya existe
        cursor.execute("SELECT * FROM usuarios WHERE username = %s", (username,))
        existe = cursor.fetchone()
        if existe:
            msg = 'El usuario ya existe'
        else:
            cursor.execute("INSERT INTO usuarios (username, password) VALUES (%s, %s)", (username, password))
            conexion.commit()
            msg = 'Usuario registrado exitosamente'
        cursor.close()
        conexion.close()
    return render_template('public/register.html', msg=msg)


#RUTAS
@app.route('/registrar-carro', methods=['GET','POST'])
def addCarro():
    return render_template('public/acciones/add.html')


 
#Registrando nuevo carro
@app.route('/carro', methods=['POST'])
def formAddCarro():
    if request.method == 'POST':
        marca               = request.form['marca']
        modelo              = request.form['modelo']
        year                = request.form['year']
        color               = request.form['color']
        puertas             = request.form['puertas']
        favorito            = request.form['favorito']
        
        
        if(request.files['foto'] !=''):
            file     = request.files['foto'] #recibiendo el archivo
            nuevoNombreFile = recibeFoto(file) #Llamado la funcion que procesa la imagen
            resultData = registrarCarro(marca, modelo, year, color, puertas, favorito, nuevoNombreFile)
            if(resultData ==1):
                return render_template('public/layout.html', miData = listaCarros(), msg='El Registro fue un éxito', tipo=1)
            else:
                return render_template('public/layout.html', msg = 'Metodo HTTP incorrecto', tipo=1)   
        else:
            return render_template('public/layout.html', msg = 'Debe cargar una foto', tipo=1)
            


@app.route('/form-update-carro/<string:id>', methods=['GET','POST'])
def formViewUpdate(id):
    if request.method == 'GET':
        resultData = updateCarro(id)
        if resultData:
            return render_template('public/acciones/update.html',  dataInfo = resultData)
        else:
            return render_template('public/login.html', miData = listaCarros(), msg='No existe el carro', tipo= 1)
    else:
        return render_template('public/login.html', miData = listaCarros(), msg = 'Metodo HTTP incorrecto', tipo=1)          
 
   
  
@app.route('/ver-detalles-del-carro/<int:idCarro>', methods=['GET', 'POST'])
def viewDetalleCarro(idCarro):
    msg =''
    if request.method == 'GET':
        resultData = detallesdelCarro(idCarro) #Funcion que almacena los detalles del carro
        
        if resultData:
            return render_template('public/acciones/view.html', infoCarro = resultData, msg='Detalles del Carro', tipo=1)
        else:
            return render_template('public/acciones/layout.html', msg='No existe el Carro', tipo=1)
    return redirect(url_for('inicio'))
    

@app.route('/actualizar-carro/<string:idCarro>', methods=['POST'])
def  formActualizarCarro(idCarro):
    if request.method == 'POST':
        marca           = request.form['marca']
        modelo          = request.form['modelo']
        year            = request.form['year']
        color           = request.form['color']
        puertas         = request.form['puertas']
        favorito        = request.form['favorito']
        
        # Verificar si se envió una foto
        foto_carro = None
        if 'foto' in request.files and request.files['foto'].filename != '':
            file = request.files['foto']
            foto_carro = recibeFoto(file)

        # Llamar a la función para actualizar el carro
        resultData = recibeActualizarCarro(
            marca, modelo, year, color, puertas, favorito, foto_carro, idCarro
        )
        
        if(resultData ==1):
            return render_template('public/layout.html', miData = listaCarros(), msg='Datos del carro actualizados', tipo=1)
        else:
            return render_template('public/layout.html', miData = listaCarros(), msg='No se pudo actualizar', tipo=1)


#Eliminar carro
@app.route('/borrar-carro', methods=['GET', 'POST'])
def formViewBorrarCarro():
    if request.method == 'POST':
        idCarro         = request.form['id']
        nombreFoto      = request.form['nombreFoto']
        resultData      = eliminarCarro(idCarro, nombreFoto)

        if resultData ==1:
            #Nota: retorno solo un json y no una vista para evitar refescar la vista
            return jsonify([1])
            #return jsonify(["respuesta", 1])
        else: 
            return jsonify([0])




def eliminarCarro(idCarro='', nombreFoto=''):
        
    conexion_MySQLdb = connectionBD() #Hago instancia a mi conexion desde la funcion
    cur              = conexion_MySQLdb.cursor(dictionary=True)
    
    cur.execute('DELETE FROM carros WHERE id=%s', (idCarro,))
    conexion_MySQLdb.commit()
    resultado_eliminar = cur.rowcount #retorna 1 o 0
    #print(resultado_eliminar)
    
    basepath = os.path.dirname (__file__) #C:\xampp\htdocs\localhost\Crud-con-FLASK-PYTHON-y-MySQL\app
    url_File = os.path.join (basepath, 'static/assets/fotos_carros', nombreFoto)
    os.remove(url_File) #Borrar foto desde la carpeta
    #os.unlink(url_File) #Otra forma de borrar archivos en una carpeta
    

    return resultado_eliminar



def recibeFoto(file):
    basepath = os.path.dirname (__file__) #La ruta donde se encuentra el archivo actual
    filename = secure_filename(file.filename) #Nombre original del archivo

    #capturando extensión del archivo ejemplo: (.png, .jpg, .pdf ...etc)
    extension           = os.path.splitext(filename)[1]
    nuevoNombreFile     = stringAleatorio() + extension
    #print(nuevoNombreFile)
        
    upload_path = os.path.join (basepath, 'static/assets/fotos_carros', nuevoNombreFile) 
    file.save(upload_path)

    return nuevoNombreFile

       
  
  
#Redireccionando cuando la página no existe
@app.errorhandler(404)
def not_found(error):
    return redirect(url_for('inicio'))
    
    
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))  
    
if __name__ == "__main__":
    app.run(debug=True, port=8000)


