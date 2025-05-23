# Generated by Django 4.1.13 on 2025-05-14 04:26

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarritoCompra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usuario', models.CharField(default='anonymous', max_length=100)),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now)),
                ('completado', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ItemCarrito',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.IntegerField(default=1)),
                ('fecha_agregado', models.DateTimeField(default=django.utils.timezone.now)),
                ('carrito', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='productos.carritocompra')),
                ('producto_sucursal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='productos.productosucursal')),
            ],
            options={
                'unique_together': {('carrito', 'producto_sucursal')},
            },
        ),
    ]
