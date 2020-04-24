# İstanbul Halk Ekmek Büfelerinin ve Satış Noktalarının Harita Üzerine İşlenmesi<br>
###### Toygar Aksoy - 2020 / 04  

"""
Bu çalışmada gerçek bir veri seti kullanılarak, adres bilgileri kullanılarak coğrafi bilgi servislerinden koordinat bilgilerinin çekilmesi ve bu verilerin işlenmesiyle bir harita oluşturulması gösterilmektedir. 

Türkçe'ye özel karakterlerin işlenmesindeki güçlükler ve veri setlerinden doğan aksaklıklar bir kenara bırakılacak olursa, geopandas ve folium modülleri ile harita oluşturmak ve işlemek oldukça kolay.

Bir harita oluşturmak için yapılması gereken işlemleri üç ana başlık altında toplayabiliriz:

1) Adres veri setinin elde edilmesi ve temizlenmesi

2) Coğrafi bilgi servislerinden koordinat bilgisinin çekilmesi ve veri setine işlenmesi

3) Bir harita oluşturulması ve çekilen koordinatların harita üzerine işlenmesi

Bu çalışma veri setinin eldesi ve temizlenmesi konusuna değinmemektedir.
"""

#İhtiyaç duyulacak modüller

import geopandas as gpd
import pandas as pd
import numpy as np
from geopandas.tools import geocode
import folium
from folium import Marker, Popup
import geopy
from branca.element import *
from IPython.display import IFrame
import branca




"""
Büfe ve satış noktaları bilgisini içeren .csv dosyasının yüklenmesi

Bu örnekte İstanbul Halk Ekmek'in adres veri setini kullandık. İşin büyük kısmını oluşturmasına rağmen, konumuzun dışında olduğu için veri setinin elde edilmesi ve temizlenmesi aşamalarından bahsetmiyoruz.
"""

dosya = "CSV_Istanbul_Halk_Ekmek_Bufeler_ve_Satis_Noktalari.csv"
data = pd.read_csv(dosya)

# Adres ve ilçe sütunundaki girdiler bizim için önemli. İdeal bir süreç için bunlardaki hatalar giderilmeli.
print(data.head())
#print(data.columns)






"""
Coğrafi bilgi servisleri testi

Coğrafi bilgi servislerinin kullanıcı adı olmadan kullanılıp doğruya yakın sonuçlar üretip üretemediğini test etmek gerekiyor. Her servis sağlayıcı aynı verimle çalışmayabiliyor, doğal dil işleme konusunda başarılı olamayabiliyor ya da belirli bölgelerle sınırlandırılmış olabiliyor. 

Bunların önceden tespit edilmesi haritanın sağlıklı oluşturulabilmesi için gerekli.
"""

for i in geopy.geocoders.SERVICE_TO_GEOCODER.keys():
    try:
        result = geocode("YAVUZ SELİM MAH.TÜRKİYE CAD NO:53-1 ", provider=i)
        point = result.geometry.iloc[0]
        
        print(i,"başarılı.")
        # Başarılı sonuç veren modüllerin aynı enlem ve boylam değerlerini ürettikleri de kontrol edilmeli.
        print("Enlem:", point.y)
        print("Boylam:", point.x,"\n")
    except:
        pass
        
#Test sonucunda ArcGIS kullanmanın daha doğru olacağı sonucuna ulaştık.






# Örnek bir adres kullanılarak sistemin test edilmesi:
# Örnek bir adresle test
result = geocode("DENİZKÖŞKLER MAH.SERÇE SK. NO:18/1", provider="arcgis")
point = result.geometry.iloc[0]
print("Enlem:", point.y)
print("Boylam:", point.x)

# Güncellenmiş bir adresle test
result = geocode("DENİZKÖŞKLER MAH.SERÇE SK. NO:18/1"+" AVCILAR"+" İSTANBUL", provider="arcgis")
point = result.geometry.iloc[0]
print("Enlem:", point.y)
print("Boylam:", point.x)


"""
Arcgis'in adres bulma işlemini daha doğru yapabilmesi için adres bilgileri ilçe ve şehir bilgisi içerecek şekilde güncellenmesi

Bu noktada adres bilgilerinde yazım hataları vs. düzeltilmeli ve servis sağlayıcılar tekrar kontol edilmeli. Böylece servis sağlayıcının Türkçe ile yaşayacağı olası sorunlar engellenmeli. Ne var ki, bu hem şu anda konumuzun dışında, hem de uzun zaman alan ve uğraştırıcı bir mesele. Dolayısıyla burada bahsedilmeyecek.
"""

# Birleştirilmiş adres bilgisi "Adres_2" adlı yeni bir sütuna kaydedildi.
data["Adres_2"] = data.apply(lambda x: (str(x['Adres'])+" "+str(x["İlçe"])+" İstanbul"), axis=1)
#print(data.Adres_2.head())

#Güncelleme işlemi bütün veri tabanına uygulandıktan sonra tekrar test edip önceki sonuçlarla aynı olup olmadığı kıyaslanıyor
result = geocode(data['Adres_2'][65], provider="arcgis")
point = result.geometry.iloc[0]
print("\nEnlem:", point.y)
print("Boylam:", point.x)



# Adres koordinatlarını veri tabanına işleyecek fonksiyon

def koordinat_isleyici(satir):
    try:
        point = geocode(satir, provider="arcgis").geometry.iloc[0]
        return pd.Series({'Enlem':point.y, 'Boylam':point.x, 'geometry':point})
    except:
        return None 




"""
Veri setinde güncellenmiş adreslerin koordinatlarının işlenmesi

koordinat_işleyici() fonksiyonu bütün veri tabanına uygulanarak adres bilgilerinden elde edilen enlem, boylam ve geometri bilgileri veri setinde yeni kolonlar üzerine işledik.
Ardından çeşitli sebeplerle bulunamamış koordinatların sayısını tespit ettik. Yapılacak işleme ve kayıp miktarına bağlı bir yol seçerek bu koordinatların başka kaynaklardan bulunması, adreslerin güncellenmesi veya bu girdilerin veri setinden çıkarılması gibi bir yol seçilmelidir. 

Bu örnekte bu gibi girdileri veri setinden çıkarmayı tercih ettik.

Veri setinin GeoDataFrame tipine dönüştürülebilmesi için bir coğrafi koordinat sisteminin işlenmesi gereklidir. Burada kullandığımız dünya çapında yaygın olarak kullanılan WGS84 projeksiyonunu "epsg:4326" argümanıyla veri setine işliyoruz. 
"""

#  koordinat_isleyici() fonksiyonu bütün veri setine uygulandı.
data[['Enlem', 'Boylam', 'geometry']] = data.apply(lambda x : koordinat_isleyici(x['Adres_2']), axis=1)

print("Adreslerin %{}'ı işlendi.".format((1-(sum(np.isnan(data['Enlem'])))/len(data))/100))





# İşlenememiş adreslerin ekrana yazdırılması
print("İşlenememiş girdilerin sayısı:",len(data.loc[np.isnan(data['Enlem'])]),"\n")
# Gerek görülürse bu kısım aktive edilerek işlenememiş adresler görüntülenebilir.
#print(data.loc[np.isnan(data['Enlem'])])

# İşlenememiş girdiler veri tabanından çıkarıldı.
data = data.loc[~np.isnan(data['Enlem'])]

# Veri tabanı 'geopandas.geodataframe.GeoDataFrame' tipine dönüştürüldü.
data = gpd.GeoDataFrame(data, geometry= data.geometry)
data.crs={'init':'epsg:4326'}

# Veri tabanının son hali.
#print(data.head())




"""
Çeşitli hatalardan dolayı bulunan bazı adresler gerçek konumlarının çok uzağında gösterilebilir. Bunun önüne geçilmesi için de daha önce bahsedilen stratejilerden biri seçilip kullanılmalı. Bu örneğin konusu değil, dolayısıyla burada İstanbul dışındaki yerlerin haritadan çıkarılması tercih edildi.
"""

# Anormal koordinatlı girdilerin sayısının bulunması
print(len(data.loc[(data['Enlem']>41.3) | (data['Enlem']<40.7) | (data['Boylam']>30.1) | (data['Boylam']<27.9)]))

# İstanbul dışındaki yerlerin haritadan çıkarılması.
data = data.loc[(data['Enlem']<41.3) & (data['Enlem']>40.7) & (data['Boylam']<30.1) & (data['Boylam']>27.9)]
# print(len(data2))






# Haritanın oluşturulması

#Önce elde ettiğimiz koordinatları işleyeceğimiz haritayı oluşturmamız gerekiyor.

harita = folium.Map(location=[41.0, 29.0], tiles='cartodbpositron', zoom_start=10)





#Şimdi de haritanın üzerine koordinatları gösterecek işaretleri yerleştiriyoruz. 

#Türkçe karakterlerin gösteriminde sorun yaşamamak için IFrame ve branca modüllerini kullanıyoruz.

for index, satir in data.iterrows():
    html = satir['Büfe Adı'].title()
    iframe = branca.element.IFrame(html=html, width=85, height=110)
    popup = folium.Popup(iframe, max_width=500)
    Marker([satir['Enlem'], satir['Boylam']], popup=popup).add_to(harita)





# Haritayı dışarı aktarmak için IPython modülünü kullanıyoruz. Bu şekilde haritamız bir dosya halinde kaydedilerek paylaşmaya ve yayınlamaya uygun hale geliyor.

def disa_aktar(m, dosya_adi):
    m.save(dosya_adi)
    return IFrame(dosya_adi, width='100%', height='500px')
    
disa_aktar(harita, "halk_ekmek_haritasi.html")

"""
Artık elimizde çalışır durumda bir harita olduğuna göre, bu noktadan sonra, haritanın hem görsel etkileyiciliğini, hem okunabilirliğini|anlaşılabilirliğini, hem de performansını arttırmak için çalışmaya başlayabiliriz. <br>Bu örnek için yapılabilecek geliştirmeler; 
* Haritayi ilçelere bölüp her seferinde bir ilçeyi ve bu ilçedeki satış noktalarını gösterecek bir mekanizma kurulabilir.
* İkonların şekli ve rengi değiştirilebilir. Bu ayrım satış noktaları ve büfeleri ayırt etmek için kullanılabilir.
* Veri seti üzerinde iyileştirmeler yapılabilir.
"""

