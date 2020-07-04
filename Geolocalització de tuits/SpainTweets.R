# Importació de paquets
library(rtweet)
library(ggplot2)
library(ggmap)
library(sp)
library(rgdal)
library(tmap)

# Paràmetres
wd <- dirname(rstudioapi::getSourceEditorContext()$path)
searchTerm <- "#iiff"
n_tweets <- 10000

# Claus API
keys_path <- paste(wd,"/keys.csv", sep="")
keys <- read.csv(keys_path, header = TRUE, sep=",", colClasses = "character")

app_name = keys$app_name
consumer_key <- keys$consumer_key
consumer_secret <- keys$consumer_secret
token <- create_token(app_name, consumer_key, consumer_secret)

register_google(keys$google_key)


# Captura de tuits
searchResults <- search_tweets(searchTerm, n=n_tweets, include_rts= FALSE,
                               token = token, geocode = lookup_coords("spain"))
tweetFrame <- as.data.frame(searchResults)
tweetFrame <- tweetFrame[tweetFrame$location!="",]
addresses <- unique(tweetFrame[,c('screen_name','location')])


# Funció per geocodificar l'adreça
getGeoDetails <- function(address, userName){
  answer <- data.frame(lat=NA, long=NA, accuracy=NA, formatted_address=NA,
                       address_type=NA, status=NA, screenName = NA)
  geo_reply = try(geocode(address, output='all', messaging=TRUE,override_limit=TRUE))
  if (class(result) == "try-error"){
    return(answer)
  }
  if (geo_reply$status != "OK"){
    return(answer)
  }
  answer$status <- geo_reply$status
  answer$lat <- geo_reply$results[[1]]$geometry$location$lat
  answer$long <- geo_reply$results[[1]]$geometry$location$lng
  if (length(geo_reply$results[[1]]$types) > 0){
    answer$accuracy <- geo_reply$results[[1]]$types[[1]]
  }
  answer$address_type <- paste(geo_reply$results[[1]]$types, collapse=',')
  answer$formatted_address <- geo_reply$results[[1]]$formatted_address
  answer$screenName <- userName
  return(answer)
}


# Geocodificació de les adreces
geocoded <- data.frame()

for (i in seq(1, nrow(addresses))){
  result <- try( getGeoDetails(addresses$location[i],addresses$screen_name[i]))
  if (class(result) != "try-error"){
    if (!is.na (result$screenName)){
      geocoded <- rbind(geocoded, result)
    } }
}

# Exportació dels tuits
tweets_file <- paste(wd,"/tweets",searchTerm,".csv", sep = "")
write.table(geocoded, tweets_file, sep=",", row.names = FALSE)

# Creació d'un objecte SpatialPointsDataFrame
coords <- geocoded[,c(2,1)]
tweets_geo <- SpatialPointsDataFrame(coords, geocoded, proj4string = CRS("+proj=longlat"))

# Dades de totes les províncies
geo_file <- paste(wd,"/../Dades/EspanyaProvincies", sep="")
spain <- readOGR(geo_file, "recintos_provinciales_inspire_peninbal_etrs89")

# Projecció de les dades de les províncies al CRS dels tuits
crs <- proj4string(tweets_geo)
spain <- spTransform(spain, CRS(crs))

# Agregació espacial de les dades
tweets_geo$cnt <- 1
tweets_spain <- aggregate(x=tweets_geo['cnt'], by= spain, FUN = sum)
spain$tweets <- tweets_spain$cnt

# Establim els valors nuls a 0
spain@data[is.na(spain$tweets),"tweets"] <- 0

# Calculem el percentatge
n <- sum(spain$tweets)
spain$tweets <- spain$tweets / n

# Representació gràfica
title <- paste("Percentatge de tuits amb:", searchTerm)
tmap::qtm(spain, fill = "tweets", fill.palette="Reds") +
  tm_legend(legend.position = c("right", "bottom"),
            main.title = titol,
            main.title.position = "center")

