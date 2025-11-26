from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        RutUsuua = request.POST.get('RutUsuua')
        password = request.POST.get('password')
        
        print(f"Intentando login con RutUsuua: {RutUsuua}")
        
        user = authenticate(request, username=RutUsuua, password=password)
        if user is not None:
            login(request, user)
            return redirect('inventario:base')
        messages.error(request, 'RUT o contraseña inválidos.')
    return render(request, 'usuario/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('usuario:login')