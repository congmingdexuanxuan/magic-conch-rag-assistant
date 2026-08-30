package com.spongebob.magic_conch_backend;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.spongebob.magic_conch_backend.mapper")
public class MagicConchBackendApplication {

    public static void main(String[] args) {
        SpringApplication.run(MagicConchBackendApplication.class, args);
    }

}
