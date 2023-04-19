import React, { useEffect, useState } from "react";
import { View, Animated, StyleSheet, Image, TouchableOpacity, Linking } from "react-native";

const SummaryBriefing = ({ text, onWordRevealed }) => {
  const words = text.split(" ");
  const animatedValues = words.map(() => new Animated.Value(0));
  const imageAnimatedValue = new Animated.Value(0);
  const italicTextAnimatedValue = new Animated.Value(0);
  const [textWidth, setTextWidth] = useState(null);

  useEffect(() => {
    if (textWidth) {
      const animations = animatedValues.map((animatedValue, index) => {
        animatedValue.addListener(({ value }) => {
          if (value > 0.5) {
            onWordRevealed(index);
          }
        });

        return Animated.timing(animatedValue, {
          toValue: 1,
          duration: 400,
          delay: index * 100,
          useNativeDriver: true,
        });
      });

      const imageAnimation = Animated.timing(imageAnimatedValue, {
        toValue: 1,
        duration: 400,
        delay: words.length * 100,
        useNativeDriver: true,
      });

      const italicTextAnimation = Animated.timing(italicTextAnimatedValue, {
        toValue: 1,
        duration: 400,
        delay: words.length * 100,
        useNativeDriver: true,
      });

      Animated.stagger(100, [...animations, imageAnimation, italicTextAnimation]).start();
    }
  }, [textWidth]);

  const onTextLayout = (e, index) => {
    const layoutWidth = e.nativeEvent.layout.x + e.nativeEvent.layout.width;
    if (layoutWidth > textWidth) {
      setTextWidth(layoutWidth);
    }
  };

  const onImagePress = async () => {
    const url = "https://apple.news/Az-cbeANRSMqqSzmsYnW-7A"; // Replace this with your desired URL
    try {
      if (await Linking.canOpenURL(url)) {
        await Linking.openURL(url);
      } else {
        console.warn(`Can't open URL: ${url}`);
      }
    } catch (error) {
      console.error(`Error opening URL: ${error}`);
    }
  };

  const imageTranslateY = imageAnimatedValue.interpolate({
    inputRange: [0, 1],
    outputRange: [20, 0],
  });

  const imageOpacity = imageAnimatedValue.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 1],
  });

  const italicTextTranslateY = italicTextAnimatedValue.interpolate({
    inputRange: [0, 1],
    outputRange: [20, 0],
  });

  const italicTextOpacity = italicTextAnimatedValue.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 1],
  });

  return (
    <View style={styles.container}>
      {words.map((word, index) => {
        const translateY = animatedValues[index].interpolate({
          inputRange: [0, 1],
          outputRange: [20, 0],
        });

        const opacity = animatedValues[index].interpolate({
          inputRange: [0, 1],
          outputRange: [0, 1],
        });

        return (
          <Animated.Text
            key={index}
            onLayout={(e) => onTextLayout(e, index)}
            style={[styles.text, { opacity, transform: [{ translateY }] }]}
          >
            {word}{" "}
          </Animated.Text>
        );
      })}
      {textWidth && (
        <TouchableOpacity activeOpacity={0.7} onPress={onImagePress}>
        <Animated.Image
          source={require("../assets/biden.jpg")} // Replace this with the path to your image
          style={[
            styles.image,
            { width: textWidth * .94, height: 200, opacity: imageOpacity, transform: [{ translateY: imageTranslateY }] },
          ]}
          resizeMode="cover"
        />
      </TouchableOpacity>
          )}
          {textWidth && (
            <Animated.Text
              style={[
                styles.italicText,
                { width: textWidth, opacity: italicTextOpacity, transform: [{ translateY: italicTextTranslateY }] },
              ]}
            >
              Biden walking out after WHO conference{/* Replace this with your desired italic text */}
            </Animated.Text>
          )}
        </View>
      );
    };
    
    const styles = StyleSheet.create({
      container: {
        flexDirection: "row",
        flexWrap: "wrap",
        paddingHorizontal: 20,
        paddingVertical: 15,
      },
      text: {
        fontSize: 16,
        lineHeight: 24,
      },
      image: {
        marginTop: 10, // Adjust the spacing between the text and image
        borderRadius: 10, // Adjust the corner radius
      },
      italicText: {
        fontStyle: "italic",
        fontSize: 14,
        lineHeight: 20,
        marginTop: 8, // Adjust the spacing between the image and the italic text
      },
    });
    
    export default SummaryBriefing;
    
