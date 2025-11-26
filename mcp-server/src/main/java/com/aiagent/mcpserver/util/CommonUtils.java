package com.aiagent.mcpserver.util;
import java.lang.reflect.Field;
import java.util.HashMap;
import java.util.Map;

public class CommonUtils {

    /**
     * Map 데이터를 지정한 클래스 타입 객체로 매핑합니다.
     * key 이름이 필드명과 일치하면 자동으로 값이 세팅됩니다.
     */
    public static <T> T mapToObject(Map<String, Object> map, Class<T> clazz) {
        try {
            T instance = clazz.getDeclaredConstructor().newInstance();

            for (Map.Entry<String, Object> entry : map.entrySet()) {
                String key = toCamelCase(entry.getKey()); // camel case 변환
                Object value = entry.getValue();

                try {
                    Field field = clazz.getDeclaredField(key);
                    field.setAccessible(true);

                    Class<?> fieldType = field.getType();
                    Object convertedValue = convertValue(value, fieldType);

                    field.set(instance, convertedValue);

                } catch (NoSuchFieldException e) {
                    // VO에 없는 필드는 무시
                    System.out.println("[INFO] 매칭되지 않는 필드: " + key);
                }
            }
            return instance;

        } catch (Exception e) {
            throw new RuntimeException("객체 매핑 실패", e);
        }
    }

    // 어떤 객체든 Map<String, Object> 로 변환
    public static Map<String, Object> objectToMap(Object obj) {
        Map<String, Object> result = new HashMap<>();

        if (obj == null) return result;

        Class<?> clazz = obj.getClass();
        Field[] fields = clazz.getDeclaredFields();

        for (Field field : fields) {
            field.setAccessible(true); // private 필드 접근 허용
            try {
                result.put(field.getName(), field.get(obj));
            } catch (IllegalAccessException e) {
                // 필요하면 로그 처리
                e.printStackTrace();
            }
        }
        return result;
    }

    /** 간단한 타입 변환 헬퍼 */
    private static Object convertValue(Object value, Class<?> fieldType) {
        if (value == null) return null;

        String str = value.toString();

        if (fieldType == Integer.class || fieldType == int.class) {
            return Integer.parseInt(str);
        } else if (fieldType == Boolean.class || fieldType == boolean.class) {
            return Boolean.parseBoolean(str);
        } else if (fieldType == Double.class || fieldType == double.class) {
            return Double.parseDouble(str);
        } else {
            return str;
        }
    }

    public static String toCamelCase(String input) {
        if (input == null || input.isEmpty()) return null;

        // 모두 소문자로 변환
        input = input.toLowerCase();

        StringBuilder result = new StringBuilder();
        boolean nextUpper = false;

        for (char c : input.toCharArray()) {
            if (c == '_' || c == '-' || c == ' ') {
                nextUpper = true;
            } else {
                if (nextUpper) {
                    result.append(Character.toUpperCase(c));
                    nextUpper = false;
                } else {
                    result.append(c);
                }
            }
        }
        return result.toString();
    }
}