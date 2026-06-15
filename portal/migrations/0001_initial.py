from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scrape_id', models.CharField(max_length=36)),
                ('scraped_at', models.DateTimeField()),
                ('source', models.CharField(db_index=True, max_length=80)),
                ('country', models.CharField(blank=True, max_length=2, null=True)),
                ('product_url', models.URLField(max_length=500)),
                ('sku', models.CharField(blank=True, max_length=100, null=True)),
                ('name', models.CharField(max_length=500)),
                ('category', models.CharField(blank=True, max_length=200, null=True)),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ('currency', models.CharField(max_length=8)),
                ('price_list', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ('availability', models.CharField(max_length=20)),
                ('stock_text', models.CharField(blank=True, max_length=500, null=True)),
                ('sizes', models.TextField(blank=True)),
                ('colors', models.TextField(blank=True)),
                ('image_url', models.URLField(blank=True, max_length=500, null=True)),
                ('raw_attributes', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Producto',
                'verbose_name_plural': 'Productos',
                'db_table': 'products',
                'ordering': ['-scraped_at'],
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ScrapeJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pendiente'), ('running', 'En curso'), ('done', 'Completado'), ('error', 'Error')], default='pending', max_length=20)),
                ('job_type', models.CharField(default='scrape', max_length=20)),
                ('country', models.CharField(default='all', max_length=10)),
                ('site_slug', models.CharField(default='all', max_length=80)),
                ('max_products', models.PositiveIntegerField(default=20)),
                ('max_pages', models.PositiveIntegerField(default=2)),
                ('do_export', models.BooleanField(default=True)),
                ('export_format', models.CharField(default='xlsx', max_length=10)),
                ('log', models.TextField(blank=True)),
                ('result_json', models.TextField(blank=True)),
                ('error_message', models.TextField(blank=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=80, unique=True)),
                ('enabled', models.BooleanField(default=True)),
                ('country', models.CharField(choices=[('AR', 'Argentina'), ('CL', 'Chile')], default='AR', max_length=2)),
                ('name', models.CharField(max_length=200)),
                ('base_url', models.URLField(max_length=500)),
                ('currency', models.CharField(default='ARS', max_length=8)),
                ('scraper', models.CharField(choices=[('tiendanube', 'TiendaNube'), ('shopify', 'Shopify'), ('woocommerce', 'WooCommerce'), ('configurable', 'Configurable (CSS)')], default='tiendanube', max_length=20)),
                ('catalog_urls', models.TextField(help_text='Una URL de catálogo por línea')),
                ('product_link_pattern', models.CharField(default='/productos/', max_length=100)),
                ('delay_seconds', models.FloatField(default=2.0)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Tienda',
                'verbose_name_plural': 'Tiendas',
                'ordering': ['country', 'name'],
            },
        ),
    ]
